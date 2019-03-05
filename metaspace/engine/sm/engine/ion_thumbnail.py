import logging
from io import BytesIO
from itertools import combinations

import numpy as np
import png
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans

ISO_IMAGE_SEL = ("SELECT iso_image_ids[1] "
                 "FROM iso_image_metrics m "
                 "JOIN job j on j.id = m.job_id "
                 "WHERE ds_id = %s "
                 "ORDER BY fdr, msm "
                 "LIMIT 500")

THUMB_SEL = "SELECT ion_thumbnail FROM dataset WHERE id = %s"

THUMB_UPD = "UPDATE dataset SET ion_thumbnail = %s WHERE id = %s"

ALGORITHMS = {
    'smart-image-medoid': lambda *args: _make_thumbnail_from_minimally_overlapping_image_clusters(*args, use_centroids=False),
    'smart-image-centroid': lambda *args: _make_thumbnail_from_minimally_overlapping_image_clusters(*args, use_centroids=True),
    'image-medoid': lambda *args: _make_thumbnail_from_image_clusters(*args, use_centroids=False),
    'image-centroid': lambda *args: _make_thumbnail_from_image_clusters(*args, use_centroids=True),
    'pixel-mean-intensity': lambda *args: _make_thumbnail_from_pixel_clusters(*args, use_distance_from_centroid=False),
    'pixel-distance': lambda *args: _make_thumbnail_from_pixel_clusters(*args, use_distance_from_centroid=True),
}
DEFAULT_ALGORITHM = 'image-centroid'

logger = logging.getLogger('engine')


def _get_good_images(images, mask):
    """ Try to discard images with very many or very few populated pixels """
    fill_factor = np.count_nonzero(images > 0.25, axis=1) / np.count_nonzero(mask)
    good_fill = (fill_factor > 0.2) * (fill_factor < 0.8)
    if np.count_nonzero(good_fill) < 20:
        good_fill = np.nonzero(fill_factor > 0)
    if np.count_nonzero(good_fill) < 20:
        good_fill = np.ones(len(images), dtype=np.bool)
    return images[good_fill]


def _pick_least_overlapping_image_set(images, mask, num_to_pick):
    pixel_count = np.count_nonzero(mask)

    def get_overlap(idxs):
        num_nonoverlapping = np.count_nonzero(np.sum([images[i] > 0.25 for i in idxs], axis=0) == 1) / pixel_count
        sum_population = np.count_nonzero(np.sum([images[i] > 0.25 for i in idxs], axis=0)) / pixel_count
        min_population = np.min([np.sum(images[i] > 0.25) for i in idxs]) / pixel_count
        return num_nonoverlapping * (1 - np.abs(0.8 - sum_population)) * min_population

    possible_choices = list(combinations(range(len(images)), num_to_pick))
    best_choice_idx = np.argmax([get_overlap(idxs) for idxs in possible_choices])
    return images[possible_choices[best_choice_idx], :]


def _sort_by_centralness(images, h, w):
    cone_h = np.abs(np.linspace(0, 2, h) - 1)[:, np.newaxis]
    cone_w = np.abs(np.linspace(0, 2, w) - 1)[np.newaxis, :]
    cone = (cone_h * cone_w).ravel()
    centralness = np.sum(images * cone[np.newaxis, :], axis=1) / np.sum(images + 0.01, axis=1)
    return images[np.argsort(centralness)]


def _make_thumbnail_from_minimally_overlapping_image_clusters(images, mask, h, w, use_centroids):
    if len(images) > 3:
        good_images = _get_good_images(images, mask)
        kmeans = KMeans(min(10, len(images)))
        kmeans.fit(good_images)
        all_centroids = kmeans.cluster_centers_
        centroids = _pick_least_overlapping_image_set(all_centroids, mask, 3)
        # centroids, labels = kmeans2(good_images, good_images[:3])
        medoids_idxs = [np.argmin(cdist(good_images, centroid[np.newaxis, :])) for centroid in centroids]
        medoids = np.array([good_images[idx] for idx in medoids_idxs])
    else:
        # Pad with zeros
        medoids = centroids = np.array([*np.zeros((3-len(images), h*w)), *images])

    # centroids are smoother and slightly nicer looking, medoids are more eye-catching but look worse in large lists
    samples = centroids if use_centroids else medoids
    # Sort by total intensity for consistency
    # samples = [samples[i] for i in np.argsort(np.sum(samples, axis=1))]
    samples = _sort_by_centralness(samples, h, w)[::-1]
    return np.dstack([*(sample.reshape(h, w) for sample in samples), mask])


def _make_thumbnail_from_image_clusters(images, mask, h, w, use_centroids):
    if len(images) > 3:
        good_images = _get_good_images(images, mask)
        kmeans = KMeans(3)
        kmeans.fit(good_images)
        centroids = kmeans.cluster_centers_
        medoids_idxs = [np.argmin(cdist(good_images, centroid[np.newaxis, :])) for centroid in centroids]
        medoids = np.array([good_images[idx] for idx in medoids_idxs])
    else:
        # Pad with zeros
        medoids = centroids = np.array([*np.zeros((3-len(images), h*w)), *images])

    # centroids are smoother and slightly nicer looking, medoids are more eye-catching but look worse in large lists
    samples = centroids if use_centroids else medoids
    # Sort by total intensity for consistency
    samples = _sort_by_centralness(samples, h, w)[::-1]
    return np.dstack([*(sample.reshape(h, w) for sample in samples), mask])


def _make_thumbnail_from_pixel_clusters(images, mask, h, w, use_distance_from_centroid=False):
    """ Alternate implementation. Results are sharper, but noisier """
    # 6-color
    # COLORS = np.array([[1, 0, 1, 0], [1, 0, 0, 0], [1, 1, 0, 0], [0, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 0]],
    #                   dtype=np.float32)
    COLORS = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]], dtype=np.float32)
    num_clusters = len(COLORS)

    pixels = images.transpose()[np.flatnonzero(mask)] # Only include unmasked pixels
    kmeans = KMeans(num_clusters)
    kmeans.fit(pixels)
    centroids = kmeans.cluster_centers_
    labels = kmeans.labels_
    labels_mask = labels[np.newaxis, :] == np.arange(num_clusters)[:, np.newaxis]
    if use_distance_from_centroid:
        # Get pixel intensity from inverse distance from centroid
        pixel_centroids = centroids[labels]
        pixel_distance_from_centroid = np.sum((pixels - pixel_centroids) ** 2, axis=1) ** 0.5
        cluster_radii = np.average(pixel_distance_from_centroid[np.newaxis, :] * labels_mask, weights=labels_mask, axis=1)
        pixel_cluster_radii = cluster_radii[labels]
        pixel_intensity = (1 - pixel_distance_from_centroid / pixel_cluster_radii)
    else:
        pixel_intensity = np.mean(pixels, axis=1)

    # Sort colors by total intensity for consistency, and normalize each label
    label_intensity = np.average(pixel_intensity[np.newaxis, :] * labels_mask, weights=labels_mask, axis=1)
    sorted_colors = COLORS[np.argsort(label_intensity)]

    pixel_vals = (sorted_colors[labels] * pixel_intensity[:, np.newaxis])
    pixel_vals[:, :3] /= np.max(pixel_vals, axis=0)[:3]

    unmasked_pixel_vals = np.zeros((w*h, 4), dtype=np.float32)
    unmasked_pixel_vals[np.flatnonzero(mask)] = pixel_vals
    unmasked_pixel_vals[:, 3] = mask.ravel()
    return unmasked_pixel_vals.reshape((h, w, 4))


def _generate_ion_thumbnail_image(db, img_store, ds_id, algorithm):
    annotation_rows = db.select(ISO_IMAGE_SEL, [ds_id])
    if not annotation_rows:
        logger.warning('Could not create ion thumbnail - no annotations found')
        return None

    image_ids = [image_id for image_id, in annotation_rows]

    # Hotspot percentile is lowered as a lazy way to brighten images
    images, mask, (h, w) = img_store.get_ion_images_for_analysis('fs', image_ids,
                                                                 max_size=(200,200), hotspot_percentile=90)

    logger.debug(f'Generating ion thumbnail: {algorithm}({len(images)} x {h} x {w}) ')
    thumbnail = ALGORITHMS[algorithm](images, mask, h, w)

    return np.uint8(np.clip(thumbnail * 255, 0, 255)).reshape((h, w, 4))


def _save_ion_thumbnail_image(img_store, thumbnail):
    h, w, depth = thumbnail.shape
    fp = BytesIO()
    png_writer = png.Writer(width=w, height=h, alpha=True, compression=9)
    png_writer.write(fp, thumbnail.reshape(h, w * depth).tolist())
    fp.seek(0)
    return img_store.post_image('fs', 'ion_thumbnail', fp)


def generate_ion_thumbnail(db, img_store, ds_id, only_if_needed=False, algorithm=DEFAULT_ALGORITHM):
    try:
        existing_thumb_id, = db.select_one(THUMB_SEL, [ds_id])

        if existing_thumb_id and only_if_needed:
            return

        thumbnail = _generate_ion_thumbnail_image(db, img_store, ds_id, algorithm)

        if thumbnail is None:
            return

        image_id = _save_ion_thumbnail_image(img_store, thumbnail)
        db.alter(THUMB_UPD, [image_id, ds_id])

        if existing_thumb_id:
            img_store.delete_image_by_id('fs', 'ion_thumbnail', existing_thumb_id)

    except Exception:
        logger.error('Error generating ion thumbnail image', exc_info=True)

