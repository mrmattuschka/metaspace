import numpy as np
from pyimzml.ImzMLParser import ImzMLParser

from sm.engine.diagnostics.diagnostics import BaseDiagnostics
from sm.engine.imzml_parser import TOTAL_ION_CURRENT_ACCESSION
from sm.engine.png_generator import PngGenerator


def stats_for(arr):
    return {
        'min': np.min(arr),
        'max': np.max(arr),
        'median': np.median(arr),
        'mean': np.mean(arr),
    }


class TICDiagnostics(BaseDiagnostics):
    type = 'TIC'
    needs_imzml = True
    needs_spectra = True

    def process_imzml(self, imzml_parser, coords, h, w, mask):
        self._coords = coords
        # coords = np.array(imzml_parser.coordinates)[:2]
        # self._min_coord = np.min(coords, axis=0)
        # max_coord = np.max(coords, axis=0)
        # h, w = max_coord - self._min_coord + (1, 1)
        self._tic = np.zeros((h, w), dtype=np.float32)

        imzml_tic = imzml_parser.spectrum_metadata_fields.get(TOTAL_ION_CURRENT_ACCESSION)
        if imzml_tic is not None and any(tic is not None for tic in imzml_tic):
            self._imzml_tic = np.zeros((h, w), dtype=np.float32)
            self._imzml_tic[coords[:, 0], coords[:, 1]] = imzml_tic

    def process_spectrum(
        self,
        imzml_parser: ImzMLParser,
        spectrum_i: int,
        x: int,
        y: int,
        mzs: np.ndarray,
        ints: np.ndarray,
    ):
        self._tic[y, x] += np.sum(ints)

    def _get_data_for_dataset(self, job_data_and_images):
        peak_stats = stats_for(self._tic)
        image_ids = []
        data = {
            'peaks_tic_stats': peak_stats,
            'imzml_tic_stats': None,
            'peaks_tic_png_idx': 0,
            'peaks_tic_npy_idx': 1,
            'imzml_tic_png_idx': None,
            'imzml_tic_npy_idx': None,
        }
        if self._imzml_tic is not None:
            imzml_stats = stats_for(self._imzml_tic)
        else:
            imzml_stats = None

        png_data = (self._tic - data['min']) / (data['max'] - data['min'])
        png_generator = PngGenerator(False, greyscale=True)
        fp = png_generator.generate_png(png_data)
        image_id = self._image_manager.post_image('fs', 'diagnostic_image', fp)

        return data, [image_id]
