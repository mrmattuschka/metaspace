from typing import Optional, List, Dict, Tuple

import numpy as np
from pyimzml.ImzMLParser import ImzMLParser

from sm.engine.diagnostics.tic import TICDiagnostics


class BaseDiagnostics:
    type = 'BASE'
    # Flags indicating what data is needed. Allows batch-generation script to skip certain steps
    # if the diagnostic being run doesn't need certain types of data
    needs_imzml = False
    needs_spectra = False
    needs_annotations = False
    needs_ion_images = False

    def __init__(self, db, image_manager, ds_id):
        self._db = db
        self._image_manager = image_manager
        self._ds_id = ds_id

    def process_imzml(
        self, imzml_parser: ImzMLParser, coords: np.ndarray, h: int, w: int, mask: np.ndarray
    ):
        """Called when the imzml file is first opened"""
        pass

    def process_spectrum(
        self,
        imzml_parser: ImzMLParser,
        spectrum_i: int,
        x: int,
        y: int,
        mzs: np.ndarray,
        ints: np.ndarray,
    ):
        """Called for each read spectrum"""
        pass

    def process_annotations(self, job, annotations):
        """Called for the full annotations dataframe for a dataset"""
        pass

    def process_ion_image(self, job, annotation, image):
        """Called for each saved annotation"""
        pass

    def get_result_for_job(self, job) -> Tuple[Optional[Dict], Optional[List[str]]]:
        """
        Returns job-specific data(JSON-serializable) and image IDs to be saved.
        """
        data, image_ids = None, None
        return data, image_ids

    def get_result_for_dataset(
        self, job_data_and_image_ids
    ) -> Tuple[Optional[Dict], Optional[List[str]]]:
        """
        Returns the non-job-specific data(JSON-serializable) and image IDs to be saved.
        Some diagnostics will have a "summarize per-job data for the whole dataset" step,
        so this accepts job_data_and_image_ids as a parameter so that previously processed job data
        can be used, even if those jobs haven't been re-processed
        """
        data, image_ids = None, None
        return data, image_ids

    def save(self):
        """
        Sync with DB using _get_data_for_job and _get_data_for_dataset
        to get the values that should be saved.
        This function probably would be common to all implementations and would just exclude
        job-specific or dataset-specific rows if nothing was returned from the _get_data methods

        _get_data_for_job may be skipped for existing jobs when a dataset is reprocessed with new DBs
        """
        pass


class DiagnosticManager:
    def __init__(self, diagnostics: List[BaseDiagnostics]):
        self.diagnostics = list(diagnostics)
        self.errors = {}
        self.needs_imzml = any(d.needs_imzml for d in self.diagnostics)
        self.needs_spectra = any(d.needs_spectra for d in self.diagnostics)
        self.needs_annotations = any(d.needs_annotations for d in self.diagnostics)
        self.needs_ion_images = any(d.needs_ion_images for d in self.diagnostics)

    def _foreach_diagnostic(self, func, *args):
        errors = {}
        for d in self.diagnostics:
            try:
                getattr(d, func)(*args)
            except Exception as ex:
                errors[d] = ex

        self.errors.update(errors)
        for k in errors.keys():
            self.diagnostics.remove(k)

    def process_imzml(self, imzml_parser):
        self._foreach_diagnostic('process_imzml', imzml_parser)

    def process_spectrum(self, imzml_parser, spectrum_i, x, y, mzs, ints):
        self._foreach_diagnostic('process_spectrum', imzml_parser, x, y, spectrum_i, mzs, ints)

    def process_annotations(self, job, annotations):
        self._foreach_diagnostic('process_annotations', job, annotations)

    def process_ion_image(self, job, annotation, image):
        self._foreach_diagnostic('process_ion_image', job, annotation, image)

    def save(self):
        self._foreach_diagnostic('save')

        # TODO: Save errors


#  LATER
# def regenerate_diagnostics(db, image_manager, ds_id):
#     diagnostic_classes = [
#         TICDiagnostics,
#         # ...
#     ]
#     diag = CompositeDiagnostics([D(db, image_manager, ds_id) for D in diagnostic_classes])
#
#     if diag.needs_imzml or diag.needs_spectra:
#         imzml_parser = ImzMLParser()
#
#         diag.process_imzml(imzml_parser)
#
#         if diag.needs_spectra:
#             min_x, min_y = np.min(imzml_parser.coordinates, axis=0)[:2]
#             for sp_i, (x, y, z) in enumerate(imzml_parser.coordinates):
#                 mzs, ints = imzml_parser.getspectrum(sp_i)
#                 diag.process_spectrum(imzml_parser, sp_i, x - min_x, y - min_y, mzs, ints)
#
#     if diag.needs_annotations or diag.needs_ion_images:
#         for job, annotations in []:
#             diag.process_annotations(job, annotations)
#             # get annotations as DF and images as iterable
#             for ann, ion_image in zip(annotations, []):
#                 diag.process_ion_image(job, ann, ion_image)
#
#     diag.save()
