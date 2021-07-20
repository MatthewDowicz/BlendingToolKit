import pytest
from conftest import data_dir

from btk.catalog import CatsimCatalog
from btk.draw_blends import CatsimGenerator
from btk.draw_blends import get_catsim_galaxy
from btk.draw_blends import SourceNotVisible
from btk.sampling_functions import DefaultSampling
from btk.sampling_functions import SamplingFunction
from btk.survey import Filter
from btk.survey import get_psf
from btk.survey import get_psf_from_file
from btk.survey import get_surveys

CATALOG_PATH = data_dir / "sample_input_catalog.fits"


def test_sampling_no_max_number():
    class TestSamplingFunction(SamplingFunction):
        def __init__(self):
            pass

        def __call__(self, table, **kwargs):
            pass

        @property
        def compatible_catalogs(self):
            return "CatsimCatalog", "CosmosCatalog"

    with pytest.raises(AttributeError) as excinfo:
        stamp_size = 24.0
        batch_size = 8
        cpus = 1
        add_noise = True

        catalog = CatsimCatalog.from_file(CATALOG_PATH)
        sampling_function = TestSamplingFunction()
        draw_generator = CatsimGenerator(
            catalog,
            sampling_function,
            get_surveys("Rubin"),
            stamp_size=stamp_size,
            batch_size=batch_size,
            cpus=cpus,
            add_noise=add_noise,
        )
        draw_output = next(draw_generator)  # noqa: F841

    assert "max_number" in str(excinfo.value)


def test_sampling_incompatible_catalog():
    class TestSamplingFunction(SamplingFunction):
        def __call__(self, table, **kwargs):
            pass

        @property
        def compatible_catalogs(self):
            return "CosmosCatalog"

    with pytest.raises(AttributeError) as excinfo:
        stamp_size = 24.0
        batch_size = 8
        cpus = 1
        add_noise = True

        catalog = CatsimCatalog.from_file(CATALOG_PATH)
        sampling_function = TestSamplingFunction(max_number=5)
        draw_generator = CatsimGenerator(
            catalog,
            sampling_function,
            get_surveys("Rubin"),
            stamp_size=stamp_size,
            batch_size=batch_size,
            cpus=cpus,
            add_noise=add_noise,
        )
        draw_output = next(draw_generator)  # noqa: F841

    assert "Your catalog and sampling functions are not compatible with each other." in str(
        excinfo.value
    )


def test_sampling_too_much_objects():
    # FAILING
    CATALOG_PATH = "data/sample_input_catalog.fits"

    class TestSamplingFunction(SamplingFunction):
        def __call__(self, table, **kwargs):
            return table[: self.max_number + 1]

        @property
        def compatible_catalogs(self):
            return "CatsimCatalog", "CosmosCatalog"

    with pytest.raises(ValueError) as excinfo:
        stamp_size = 24.0
        batch_size = 8
        cpus = 1
        add_noise = True

        catalog = CatsimCatalog.from_file(CATALOG_PATH)
        sampling_function = TestSamplingFunction(max_number=5)
        draw_generator = CatsimGenerator(
            catalog,
            sampling_function,
            get_surveys("Rubin"),
            stamp_size=stamp_size,
            batch_size=batch_size,
            cpus=cpus,
            add_noise=add_noise,
        )
        draw_output = next(draw_generator)  # noqa: F841

    assert "Number of objects per blend must be less than max_number" in str(excinfo.value)


def test_source_not_visible():
    filt = Filter(
        name="u",
        psf=get_psf(
            mirror_diameter=8.36,
            effective_area=32.4,
            filt_wavelength=3592.13,
            fwhm=0.859,
        ),
        sky_brightness=22.9,
        exp_time=1680,
        zeropoint=9.16,
        extinction=0.451,
    )
    catalog = CatsimCatalog.from_file(CATALOG_PATH)
    with pytest.raises(SourceNotVisible):
        gal = get_catsim_galaxy(  # noqa: F841
            catalog.table[0], filt, get_surveys("Rubin"), True, True, True
        )


def test_survey_not_list():
    stamp_size = 24.0
    batch_size = 8
    cpus = 1
    add_noise = True

    catalog = CatsimCatalog.from_file(CATALOG_PATH)
    sampling_function = DefaultSampling(stamp_size=stamp_size)
    with pytest.raises(TypeError):
        draw_generator = CatsimGenerator(
            catalog,
            sampling_function,
            3,
            stamp_size=stamp_size,
            batch_size=batch_size,
            cpus=cpus,
            add_noise=add_noise,
        )
        draw_output = next(draw_generator)  # noqa: F841


def test_psf():
    get_psf(
        mirror_diameter=8.36,
        effective_area=32.4,
        filt_wavelength=7528.51,
        fwhm=0.748,
        atmospheric_model="Moffat",
    )
    get_psf(
        mirror_diameter=8.36,
        effective_area=32.4,
        filt_wavelength=7528.51,
        fwhm=0.748,
        atmospheric_model=None,
    )
    with pytest.raises(NotImplementedError) as excinfo:
        get_psf(
            mirror_diameter=8.36,
            effective_area=32.4,
            filt_wavelength=7528.51,
            fwhm=0.748,
            atmospheric_model="Layered",
        )

    assert "atmospheric model request" in str(excinfo.value)

    with pytest.raises(RuntimeError) as excinfo:
        get_psf(mirror_diameter=1, effective_area=4, filt_wavelength=7528.51, fwhm=0.748)

    assert "Incompatible effective-area and mirror-diameter values." in str(excinfo.value)

    with pytest.raises(RuntimeError) as excinfo:
        get_psf(
            mirror_diameter=0,
            effective_area=0,
            filt_wavelength=7528.51,
            fwhm=0.748,
            atmospheric_model=None,
        )

    assert "Neither the atmospheric nor the optical PSF components are defined." in str(
        excinfo.value
    )

    get_psf(mirror_diameter=0, effective_area=0, filt_wavelength=7528.51, fwhm=0.748)

    get_psf_from_file("tests/example_psf", get_surveys("Rubin"))
    get_psf_from_file("tests/multi_psf", get_surveys("Rubin"))
    # The case where the folder is empty cannot be tested as you cannot add an empty folder to git