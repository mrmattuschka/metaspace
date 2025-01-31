import logging
from collections import defaultdict
from typing import Dict, Optional

import numpy as np
import cpyMSpec as cpyMSpec_0_4_2
import cpyMSpec_0_3_5
from pyMSpec.pyisocalc import pyisocalc

from sm.engine.ds_config import DSConfig

assert cpyMSpec_0_4_2.utils.VERSION == '0.4.2'
assert cpyMSpec_0_3_5.utils.VERSION == '0.3.5'


logger = logging.getLogger('engine')

SIGMA_TO_FWHM = 2.3548200450309493  # 2 \sqrt{2 \log 2}
BASE_MZ = 200.0


class IsocalcWrapper:
    """Wrapper around pyMSpec.pyisocalc.pyisocalc used for getting theoretical isotope peaks'
    centroids and profiles for a sum formula.
    """

    _all_centroids_caches: Optional[Dict] = None

    @classmethod
    def set_centroids_cache_enabled(cls, enabled):
        """Turns on/off the centroids cache. This cache can become a massive memory leak
        if permanently left active. It should only be used for batch processing jobs"""
        if enabled and not cls._all_centroids_caches:
            cls._all_centroids_caches = defaultdict(dict)
        else:
            cls._all_centroids_caches = None

    def __init__(self, ds_config: DSConfig):
        self.analysis_version = ds_config.get('analysis_version', 1)

        isocalc_config = ds_config['isotope_generation']
        self.instrument = isocalc_config.get('instrument', 'TOF')
        self.charge = isocalc_config['charge']
        self.sigma = float(isocalc_config['isocalc_sigma'])
        self.n_peaks = isocalc_config['n_peaks']

        self.ppm = ds_config['image_generation']['ppm']
        centroids_cache_key = (self.charge, self.sigma, self.n_peaks, self.analysis_version)
        if self._all_centroids_caches:
            # pylint: disable=unsubscriptable-object
            self._centroids_cache = self._all_centroids_caches[centroids_cache_key]
        else:
            self._centroids_cache = None

    @staticmethod
    def _trim(mzs, ints, k):
        """Only keep top k peaks"""
        int_order = np.argsort(ints)[::-1]
        mzs = mzs[int_order][:k]
        ints = ints[int_order][:k]
        mz_order = np.argsort(mzs)
        mzs = mzs[mz_order]
        ints = ints[mz_order]
        return mzs, ints

    def _centroids_uncached(self, formula):
        """
        Args
        -----
        formula : str

        Returns
        -----
            Tuple[np.ndarray, np.ndarray]
        """
        if self.analysis_version < 2:
            cpyMSpec = cpyMSpec_0_3_5  # pylint: disable=invalid-name
        else:
            # noinspection PyPep8Naming
            cpyMSpec = cpyMSpec_0_4_2  # pylint: disable=invalid-name

        try:
            pyisocalc.parseSumFormula(formula)  # tests that formula is parsable

            iso_pattern = cpyMSpec.isotopePattern(str(formula))
            iso_pattern.addCharge(int(self.charge))
            fwhm = self.sigma * SIGMA_TO_FWHM

            if self.analysis_version < 2:
                resolving_power = iso_pattern.masses[0] / fwhm
                instrument_model = cpyMSpec.InstrumentModel('tof', resolving_power)
            else:
                resolving_power = BASE_MZ / fwhm
                instrument_model = cpyMSpec.InstrumentModel(
                    self.instrument.lower(), resolving_power, at_mz=BASE_MZ
                )

            centr = iso_pattern.centroids(instrument_model)
            mzs_ = np.array(centr.masses)
            ints_ = 100.0 * np.array(centr.intensities)
            mzs_, ints_ = self._trim(mzs_, ints_, self.n_peaks)

            n = len(mzs_)
            mzs = np.zeros(self.n_peaks)
            mzs[:n] = np.array(mzs_)
            ints = np.zeros(self.n_peaks)
            ints[:n] = ints_

            return mzs, ints

        except Exception as e:
            logger.warning(f'{formula} - {e}')
            return None, None

    def centroids(self, formula):
        if self._centroids_cache is not None:
            result = self._centroids_cache.get(formula)
            if not result:
                result = self._centroids_uncached(formula)
                # pylint: disable=unsupported-assignment-operation
                self._centroids_cache[formula] = result
            return result

        return self._centroids_uncached(formula)

    def mass_accuracy_bounds(self, mzs):
        if self.analysis_version < 2 or self.instrument == 'FTICR':
            half_width = mzs * self.ppm * 1e-6
        elif self.instrument == 'Orbitrap':
            half_width = np.sqrt(mzs / BASE_MZ) * (BASE_MZ * self.ppm * 1e-6)
        else:
            half_width = BASE_MZ * self.ppm * 1e-6

        lower = mzs - half_width
        upper = mzs + half_width
        return lower, upper
