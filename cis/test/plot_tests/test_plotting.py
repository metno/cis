"""
Module to do integration tests of plots, checking that the outputs look right.
"""
from cis.cis_main import plot_cmd
from cis.parse import parse_args
from cis.test.integration_test_data import *
from cis.test.integration.base_integration_test import BaseIntegrationTest
from cis.data_io.products.AProduct import ProductPluginException
from cis.exceptions import InvalidDimensionError
from nose.tools import raises
from unittest import skipIf
from sys import platform

import shutil
import logging

import matplotlib
import matplotlib.testing.compare as mcompare
import matplotlib.pyplot as plt

# Whether to display matplotlib output to the screen.
_DISPLAY_FIGURES = False

plt.switch_backend('agg')

skip_osx = skipIf(platform == 'darwin', 'Binary install of shapely is creating a number of failing tests on OS X.')

class VisualTest(BaseIntegrationTest):

    _DEFAULT_IMAGE_TOLERANCE = 0.2

    def setUp(self):
        # Make sure we have no unclosed plots from previous tests before
        # generating this one.
        if _DISPLAY_FIGURES:
            plt.close('all')

    def tearDown(self):
        # If a plotting test bombs out it can leave the current figure
        # in an odd state, so we make sure it's been disposed of.
        if _DISPLAY_FIGURES:
            plt.close('all')

    def check_graphic(self, tol=_DEFAULT_IMAGE_TOLERANCE):
        """Checks the CRC matches for the current matplotlib.pyplot figure, and closes the figure."""

        test_id = self.id()

        figure = plt.gcf()

        try:
            expected_fname = os.path.join(os.path.dirname(__file__),
                                          'reference', 'visual_tests',
                                          test_id + '.png')

            if not os.path.isdir(os.path.dirname(expected_fname)):
                os.makedirs(os.path.dirname(expected_fname))

            #: The path where the images generated by the tests should go.
            image_output_directory = os.path.join(os.path.dirname(__file__),
                                                  'result_image_comparison')
            if not os.access(image_output_directory, os.W_OK):
                if not os.access(os.getcwd(), os.W_OK):
                    raise IOError('Write access to a local disk is required '
                                  'to run image tests.  Run the tests from a '
                                  'current working directory you have write '
                                  'access to to avoid this issue.')
                else:
                    image_output_directory = os.path.join(os.getcwd(), 'result_image_comparison')
            result_fname = os.path.join(image_output_directory, test_id + '.png')

            if not os.path.isdir(os.path.dirname(result_fname)):
                # Handle race-condition where the directories are
                # created sometime between the check above and the
                # creation attempt below.
                try:
                    os.makedirs(os.path.dirname(result_fname))
                except OSError as err:
                    # Don't care about "File exists"
                    if err.errno != 17:
                        raise

            # Output filename if the test output a file itself (using -o)
            output_fname = os.path.join(os.path.dirname(__file__),test_id+'.png')
            # If the test created an output file itself then move that to the results folder, otherwise create an output
            if os.path.exists(output_fname):
                shutil.move(os.path.join(os.path.dirname(__file__),test_id+'.png'), result_fname)
            else:
                figure.savefig(result_fname)

            if not os.path.exists(expected_fname):
                logging.warn('Created image for test %s' % test_id)
                shutil.copy2(result_fname, expected_fname)

            try:
                err = mcompare.compare_images(expected_fname, result_fname, tol=tol)
            except ValueError:
                failed_name = mcompare.make_test_filename(result_fname, 'failed-diff')
                shutil.copy2(os.path.join(os.path.dirname(__file__),
                                          'reference', 'kitten.png'), failed_name)
                err = "Images differ in size and so are not comparable"

            if _DISPLAY_FIGURES:
                if err:
                    print('Image comparison would have failed. Message: %s' % err)
                plt.show()
            else:
                assert not err, 'Image comparison failed. Message: %s' % err

        finally:
            plt.close()


class TestPlotVisual(VisualTest):

    def test_iris_comparative_scatter(self):
        arguments = ["plot", "rain:" + valid_2d_filename + ":color=green,itemstyle=^",
                    "snow:" + valid_2d_filename, "--type", "comparativescatter", "--itemwidth", "400",
                    "--logx", "--logy", "--output", self.id() + ".png"]

        main_arguments = parse_args(arguments)
        plot_cmd(main_arguments)

        self.check_graphic()

    @skip_osx
    def test_iris_contour(self):
        arguments = ["plot", "rain:" + valid_2d_filename + ":cmap=RdBu", "--type", "contour",
                     "--xlabel", "Overidden X Label", "--title", "Overidded Title",
                    "--height", "5", "--width", "5", "--xmin", "15", "--xmax", "45", "--xstep", "20", "--cbarorient",
                     "vertical", "--fontsize", "10", "--output", self.id() + ".png"]

        main_arguments = parse_args(arguments)
        plot_cmd(main_arguments)

        self.check_graphic()

    @skip_osx
    def test_iris_contourf(self):
        arguments = ["plot", "rain:" + valid_2d_filename, "--type", "contourf",
                     "--ylabel", "Overidden Y Label", "--height", "5", "--width", "10", "--ymin", "15", "--ymax", "45",
                     "--ystep", "10", "--nocolourbar", "--output", self.id() + ".png"]

        main_arguments = parse_args(arguments)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_iris_heatmap(self):
        arguments = ["plot", "rain:" + valid_2d_filename + ":cmap=RdBu", "--type", "heatmap",
                     "--ylabel", "Overidden Y", "--title", "OveriddenTitle",
                     "--height", "3.5", "--width", "3.5", "--vmax", "0.000135", "--fontsize", "10", "--output",
                     self.id() + ".png"]

        main_arguments = parse_args(arguments)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_iris_heatmap_force_minus_180_to_180(self):
        arguments = ["plot", "rain:" + valid_2d_filename + ":cmap=RdBu", "--type", "heatmap",
                     "--ylabel", "Overidden Y", "--title", "OveriddenTitle", "--xmin", "-180", "--xmax", "180",
                     "--height", "3.5", "--width", "3.5", "--vmax", "0.000135", "--fontsize", "10", "--output",
                     self.id() + ".png"]

        main_arguments = parse_args(arguments)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_iris_histogram2d(self):
        opts = "--xmin=-50 --xmax 50 --xbinwidth 10 --ymin 1 --logy --output".split() + [self.id() + ".png"]
        arguments = ["plot", "rain:" + valid_1d_filename + ":color=red,itemstyle=step,label=overridenlabel",
                    "snow:" + valid_1d_filename + ":color=green,itemstyle=step", "--type", "histogram2d"] + opts

        main_arguments = parse_args(arguments)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_iris_histogram3d(self):
        opts = "--cmap RdBu --ylabel overiddeny --title overiddentitle --xmin 0.000002 --xmax 0.000006 " \
               "--ybinwidth 0.000001 --output ".split() + [self.id() + ".png"]
        arguments = ["plot", "rain:" + valid_1d_filename, "snow:" + valid_1d_filename, "--type", "histogram3d"] + opts

        main_arguments = parse_args(arguments)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_iris_many_lines(self):
        opts = "--xlabel overiddenxlabel --ylabel overiddenylabel --itemwidth 5 --width 10 --logy --grid " \
               "--ymin 0.00000000001 --xmax 50 --output".split() + [self.id() + ".png"]
        arguments = ["plot", "rain:" + valid_1d_filename + ":color=red",
                     "snow:" + valid_1d_filename + ":itemstyle=dashed,label=overiddenlabel2"] + opts

        main_arguments = parse_args(arguments)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_iris_one_line(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--xlabel overiddenxlabel --title overiddentitle --itemwidth 4 --height 5 --width 10 --logx" \
               " --grid".split()
        arguments = ["plot", "rain:" + valid_1d_filename + ":itemstyle=dashed,label=overiddenlabel"]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_iris_one_line_with_step(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--ystep 0.00001 --xstep 25".split()
        arguments = ["plot", "rain:" + valid_1d_filename ]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_iris_scatter2d(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type scatter --title overiddentitle --fontsize 10 --width 7 --itemwidth 300 --ymin=-0.0005" \
               " --ymax 0.0005".split()
        arguments = ["plot", "rain:" + valid_1d_filename + ":itemstyle=^"]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_iris_scatter3d(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type scatter --fontsize 7 --cbarorient vertical --grid --ymin 0 --ymax 90 --vmin 0" \
               " --cbarorient vertical".split()
        arguments = ["plot", "rain:" + valid_2d_filename + ":cmap=RdBu",
                     "snow:" + valid_2d_filename + ":label=snowlabel,cmap=RdBu"]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_other_comparative_scatter(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = " --type comparativescatter --xlabel overiddenx --ylabel overiddeny --title overiddentitle --fontsize 7" \
               " --height 5 --width 5 --xmin 0 --xmax 1 --ymin 0 --ymax 0.5 --itemwidth 400 --grid".split()
        arguments = ["plot", "AOT_440:" + valid_aeronet_filename + ":color=red,itemstyle=s",
                     "AOT_870:" + valid_aeronet_filename]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_other_contour(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type contour --ylabel overiddenylabel --title overiddentitle --vmin 0 --cbarorient vertical --grid" \
               " --xaxis Latitude --yaxis Height".split()
        arguments = ["plot", "RVOD_liq_water_content:" + valid_cloudsat_RVOD_file + ":cmap=RdBu"]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_other_contourf(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type contourf --xlabel overiddenxlabel --itemwidth 4 --fontsize 15 --height 10 --ymin 0 --ymax 10000" \
               " --vmin 0 --vstep 300 --cbarorient horizontal --grid --xaxis Latitude --yaxis Height".split()
        arguments = ["plot", "RVOD_liq_water_content:" + valid_cloudsat_RVOD_file + ":cmap=RdBu"]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_other_histogram2d(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type histogram2d --xlabel overiddenx --fontsize 10 --height 10 --width 10 --xmin 0 --xmax 1.5" \
               " --xbinwidth 0.1 --grid".split()
        arguments = ["plot", "AOT_440:" + valid_aeronet_filename + ":itemstyle=step"]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_other_histogram2d_bin_width(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = " --type histogram2d --xbinwidth 0.5".split()
        arguments = ["plot", "AOT_440:" + valid_aeronet_filename + ":itemstyle=step",
                     "AOT_870:" + valid_aeronet_filename + ":itemstyle=step"]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_other_histogram3d(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type histogram3d --xlabel overridenx --ylabel overiddeny --cbarlabel overiddencbarlabel " \
               "--title overiddentitle --fontsize 7 --width 10 --xmin 0 --xmax 2 --xbinwidth 0.1 --ymin 0 --ymax 1.5" \
               " --ybinwidth 0.1 --vmin 60 --vmax 480 --vstep 30 --cbarorient Vertical --grid".split()
        arguments = ["plot", "AOT_440:" + valid_aeronet_filename, "AOT_870:" + valid_aeronet_filename]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_other_histogram3d_doesnt_plot_coastlines(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type histogram3d".split()
        arguments = ["plot", "RVOD_liq_water_content:" + valid_cloudsat_RVOD_file, "Height:" + valid_cloudsat_RVOD_file]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_other_many_scatter_points(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type scatter --ylabel overiddenylabel --itemwidth 20 --ymin 0.1 --ymax 1 --logx --logy".split()
        arguments = ["plot", "AOT_440:" + valid_aeronet_filename,
                     "AOT_870:" + valid_aeronet_filename + ":itemstyle=x"]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_other_many_scatter_points_given_color(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type scatter --ylabel overiddenylabel --itemwidth 4 --ymin 0.1 --ymax 1 --logx --logy".split()
        arguments = ["plot", "AOT_440:" + valid_aeronet_filename,
                     "AOT_870:" + valid_aeronet_filename + ":color=blue,itemstyle=x"]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_other_many_lines(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type line --ylabel overiddenylabel --itemwidth 2 --ymin 0.1 --ymax 1 --logx --logy".split()
        arguments = ["plot", "AOT_440:" + valid_aeronet_filename + ":color=green,itemstyle=dotted",
                     "AOT_870:" + valid_aeronet_filename + ":itemstyle=dashed",
                     "AOT_1020:" + valid_aeronet_filename + ":color=red"]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_other_one_line(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type line --xlabel overiddenx --title overiddentitle --itemwidth 4 --fontsize 7 --height 7" \
               " --ymin 0.1 --ymax 1 --logx --logy".split()
        arguments = ["plot", "AOT_440:" + valid_aeronet_filename + ":itemstyle=dashed,label=overiddenlabel"]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_other_scatter2d(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type scatter --xlabel overiddenx --ylabel overiddeny --title overiddentitle --itemwidth 2" \
               " --fontsize 15 --height 5 --width 6 --logy --grid".split()
        arguments = ["plot", "AOT_440:" + valid_aeronet_filename]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_other_scatter3d(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type scatter --title overiddentitle --itemwidth 20 --vmax 175 --logy --xaxis Latitude" \
               " --yaxis Height".split()
        arguments = ["plot", "RVOD_liq_water_content:" + valid_cloudsat_RVOD_file + ":cmap=RdBu"]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_other_longitude_wrapping_0_360(self):
        """
        Test that ungridded data which crosses the dateline gets plotted correctly
        """
        from cis.test.util.mock import make_regular_2d_ungridded_data
        from cis.plotting import Plotter

        data = make_regular_2d_ungridded_data(lon_dim_length=90, lon_min=5., lon_max=325., lat_min=-30, lat_max=30)

        Plotter([data], x_variable='longitude', y_variable='latitude', plotwidth=8, plotheight=6, cbarscale=None,
                itemwidth=50, yrange={'ymin':-90, 'ymax':90},
                datagroups=[{'itemstyle':'', 'cmap':'jet', 'edgecolor':''}])

        self.check_graphic()

    def test_other_longitude_wrapping_0_360_forced_minus_180_to_180(self):
        """
        Test that ungridded data which crosses the dateline gets plotted correctly
        """
        from cis.test.util.mock import make_regular_2d_ungridded_data
        from cis.plotting import Plotter

        data = make_regular_2d_ungridded_data(lon_dim_length=90, lon_min=5., lon_max=325., lat_min=-30, lat_max=30)

        Plotter([data], x_variable='longitude', y_variable='latitude', plotwidth=8, plotheight=6, cbarscale=None,
                itemwidth=50, yrange={'ymin':-90, 'ymax':90}, xrange={'xmin':-180,'xmax':180},
                datagroups=[{'itemstyle':'', 'cmap':'jet', 'edgecolor':''}])

        self.check_graphic()

    def test_other_longitude_wrapping_minus_180_180(self):
        """
        Test that ungridded data which crosses the dateline gets plotted correctly
        """
        from cis.plotting import Plotter
        from cis.test.util.mock import make_regular_2d_ungridded_data

        data = make_regular_2d_ungridded_data(lat_dim_length=2, lon_dim_length=90, lon_min=-175., lon_max=145.)

        Plotter([data], x_variable='longitude', y_variable='latitude', plotwidth=8, plotheight=6, cbarscale=None,
                itemwidth=50, yrange={'ymin':-90, 'ymax':90},
                datagroups=[{'itemstyle':'', 'cmap':'jet', 'edgecolor':''}])

        self.check_graphic()

    def test_other_longitude_wrapping_minus_180_180_forced_0_to_360(self):
        """
        Test that ungridded data which crosses the dateline gets plotted correctly
        """
        from cis.plotting import Plotter
        from cis.test.util.mock import make_regular_2d_ungridded_data

        data = make_regular_2d_ungridded_data(lat_dim_length=2, lon_dim_length=90, lon_min=-175., lon_max=145.)

        Plotter([data], x_variable='longitude', y_variable='latitude', plotwidth=8, plotheight=6, cbarscale=None,
                itemwidth=50, yrange={'ymin':-90, 'ymax':90}, xrange={'xmin':0,'xmax':360},
                datagroups=[{'itemstyle':'', 'cmap':'jet', 'edgecolor':''}])

        self.check_graphic()

    def test_bluemarble_minus_180_180(self):
        """
        Test that ungridded data which crosses the dateline gets plotted correctly
        """
        from cis.plotting import Plotter
        from cis.test.util.mock import make_regular_2d_ungridded_data

        data = make_regular_2d_ungridded_data(lat_dim_length=2, lon_dim_length=90, lon_min=-175., lon_max=145.)

        Plotter([data], x_variable='longitude', y_variable='latitude', plotwidth=8, plotheight=6, cbarscale=None,
                itemwidth=50, yrange={'ymin':-90, 'ymax':90}, nasabluemarble=True,
                datagroups=[{'itemstyle':'', 'cmap':'jet', 'edgecolor':''}])

        self.check_graphic()

    def test_bluemarble_0_360(self):
        """
        Test that ungridded data which crosses the dateline gets plotted correctly
        """
        from cis.test.util.mock import make_regular_2d_ungridded_data
        from cis.plotting import Plotter

        data = make_regular_2d_ungridded_data(lon_dim_length=90, lon_min=5., lon_max=325., lat_min=-30, lat_max=30)

        Plotter([data], x_variable='longitude', y_variable='latitude', plotwidth=8, plotheight=6, cbarscale=None,
                itemwidth=50, yrange={'ymin':-90, 'ymax':90}, nasabluemarble=True,
                datagroups=[{'itemstyle':'', 'cmap':'jet', 'edgecolor':''}])

        self.check_graphic()

    def test_coastline_color(self):
        """
        Test that ungridded data which crosses the dateline gets plotted correctly
        """
        from cis.test.util.mock import make_regular_2d_ungridded_data
        from cis.plotting import Plotter

        data = make_regular_2d_ungridded_data(lon_dim_length=90, lon_min=5., lon_max=325., lat_min=-30, lat_max=30)

        Plotter([data], x_variable='longitude', y_variable='latitude', plotwidth=8, plotheight=6, cbarscale=None,
                itemwidth=50, yrange={'ymin':-90, 'ymax':90}, coastlinescolour='red',
                datagroups=[{'itemstyle':'', 'cmap':'jet', 'edgecolor':''}])

        self.check_graphic()

    def test_other_longitude_wrapping_multiple_ranges_forced_0_to_360(self):
        """
        Test that ungridded data which crosses the dateline gets plotted correctly
        """
        from cis.plotting import Plotter
        from cis.test.util.mock import make_regular_2d_ungridded_data

        datas = [make_regular_2d_ungridded_data(lat_dim_length=2, lon_dim_length=90, lon_min=-175., lon_max=145.),
                 make_regular_2d_ungridded_data(lon_dim_length=90, lon_min=5., lon_max=325., lat_min=30, lat_max=60)]

        Plotter(datas, x_variable='longitude', y_variable='latitude', plotwidth=8, plotheight=6, cbarscale=None,
                itemwidth=50, yrange={'ymin':-90, 'ymax':90}, xrange={'xmin':0,'xmax':360},
                datagroups=[{'itemstyle':'', 'cmap':'jet', 'edgecolor':'', 'label': '-180to180'},
                            {'itemstyle':'', 'cmap':'jet', 'edgecolor':'', 'label': '0to360'}])

        self.check_graphic()

    def test_other_longitude_wrapping_multiple_ranges_forced_minus_180_to_180(self):
        """
        Test that ungridded data which crosses the dateline gets plotted correctly
        """
        from cis.plotting import Plotter
        from cis.test.util.mock import make_regular_2d_ungridded_data

        datas = [make_regular_2d_ungridded_data(lat_dim_length=2, lon_dim_length=90, lon_min=-175., lon_max=145.),
                 make_regular_2d_ungridded_data(lon_dim_length=90, lon_min=5., lon_max=325., lat_min=30, lat_max=60)]

        Plotter(datas, x_variable='longitude', y_variable='latitude', plotwidth=8, plotheight=6, cbarscale=None,
                itemwidth=50, yrange={'ymin':-90, 'ymax':90}, xrange={'xmin':-180,'xmax':180},
                datagroups=[{'itemstyle':'', 'cmap':'jet', 'edgecolor':'', 'label': '-180to180'},
                            {'itemstyle':'', 'cmap':'jet', 'edgecolor':'', 'label': '0to360'}])

        self.check_graphic()

    @skip_osx
    def test_iris_contour_over_heatmap(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type overlay --plotwidth 20 --plotheight 15 --cbarscale 0.5".split()

        arguments = ["plot", "rain:" + valid_2d_filename + ":type=heatmap",
                     "solarupclear:" + valid_2d_filename + ":type=contour,color=white,contlevels=[1,10,25,50,175]"]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    @skip_osx
    def test_iris_contour_over_heatmap_binary_cmap(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type overlay --xmin -180 --xmax 180 --plotwidth 20 --plotheight 15 --cbarscale 0.5".split()

        arguments = ["plot", "rain:" + valid_2d_filename + ":type=heatmap,cmap=binary",
                     "solarupclear:" + valid_2d_filename + ":type=contour,cmap=jet,contlevels=[1,10,25,50,175]"]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    @skip_osx
    def test_transparent_contour_over_bluemarble(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type overlay --xmin -180 --xmax 180 --plotwidth 20 --plotheight 15 --cbarscale 0.5" \
               " --nasabluemarble".split()

        arguments = ["plot", "rain:" + valid_2d_filename + ":cmap=Reds,type=contourf,transparency=0.5,cmin=0.000075"]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    @skip_osx
    def test_filled_contour_over_scatter(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type overlay --plotwidth 20 --plotheight 15 --xaxis longitude --yaxis latitude --xmin -180 --xmax -90" \
               " --ymin 0 --ymax 90 --itemwidth 20".split()

        arguments = ["plot", "GGALT:" + valid_NCAR_NetCDF_RAF_filename + ":type=scatter",
                     "solarupclear:" + valid_2d_filename + ":type=contourf,contlevels=[0,10,20,30,40,50,100],transparency=0.7,"
                                              "contlabel=true,contfontsize=18"]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    @skip_osx
    def test_filled_contour_over_scatter_with_cmin(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type overlay --plotwidth 20 --plotheight 15 --xaxis longitude --yaxis latitude --xmin -180" \
               " --xmax -90 --ymin 0 --ymax 90 --itemwidth 20 --nasabluemarble".split()

        arguments = ["plot", "GGALT:" + valid_NCAR_NetCDF_RAF_filename + ":type=scatter",
                     "solarupclear:" + valid_2d_filename + ":type=contourf,contlevels=[40,50,100],transparency=0.3,contlabel=true,"
                                              "contfontsize=18,cmap=Reds"]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_iris_scatter_overlay(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type overlay --xlabel overiddenxlabel --height 10 --width 12 --xmin 0 --xmax 200 --xstep 10" \
               " --cbarorient horizontal --ymin 0 --ymax 90 --vmin 0 --cbarorient horizontal --itemwidth=3".split() + \
               ["--title=Overlay test"]
        arguments = ["plot", "rain:" + valid_2d_filename + ":type=heatmap" ,
                     "snow:" + valid_2d_filename + ":type=scatter,itemstyle=^,label=snowlabel"]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_medium_plot_region(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type scatter --plotwidth 20 --plotheight 15 --xaxis longitude --yaxis latitude --xmin -170 --xmax -150" \
               " --ymin 50 --ymax 70 --itemwidth 10".split()

        arguments = ["plot", "GGALT:" + valid_NCAR_NetCDF_RAF_filename]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_small_plot_region(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type scatter --plotwidth 20 --plotheight 15 --xaxis longitude --yaxis latitude --xmin -152 --xmax -150" \
               " --ymin 59 --ymax 61 --itemwidth 10".split()

        arguments = ["plot", "GGALT:" + valid_NCAR_NetCDF_RAF_filename]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_very_small_plot_region(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type scatter --plotwidth 20 --plotheight 15 --xaxis longitude --yaxis latitude --xmin -151.5 --xmax -151.2" \
               " --ymin 60.4 --ymax 60.8 --itemwidth 10".split()

        arguments = ["plot", "GGALT:" + valid_NCAR_NetCDF_RAF_filename]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_medium_plot_region_bluemarble(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type scatter --plotwidth 20 --plotheight 15 --xaxis longitude --yaxis latitude --xmin -170 --xmax -150" \
               " --ymin 50 --ymax 70 --itemwidth 10 --nasabluemarble".split()

        arguments = ["plot", "GGALT:" + valid_NCAR_NetCDF_RAF_filename]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_small_plot_region_bluemarble(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = "--type scatter --plotwidth 20 --plotheight 15 --xaxis longitude --yaxis latitude --xmin -152 --xmax -150" \
               " --ymin 59 --ymax 61 --itemwidth 10 --nasabluemarble".split()

        arguments = ["plot", "GGALT:" + valid_NCAR_NetCDF_RAF_filename]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_aerosol_cci_default_axes(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = []

        arguments = ["plot", valid_aerosol_cci_variable + ":" + valid_aerosol_cci_filename]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_aeronet_default_axes(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = []

        arguments = ["plot", valid_aeronet_variable + ":" + valid_aeronet_filename]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_multiple_time_series_default_axes(self):
        # JASCIS-231
        output_file_opt = ["--output", self.id() + ".png"]
        opts = []

        arguments = ["plot", valid_aeronet_variable + ":" + another_valid_aeronet_filename,
                     'AOT_440:' + os.path.join(data_directory, 'Abracos_Hill_AOT_6_hourly.nc')]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    @raises(InvalidDimensionError)
    def test_multiple_time_series_incompatible_axes_line(self):
        # JASCIS-231
        output_file_opt = ["--output", self.id() + ".png"]
        opts = ['--type=line']

        # The aggregated data has some guessed axis labels (x and y are lon and lat respectively) which don't
        #  correspond to the other aeronet file, so this should be caught and related to the user.
        arguments = ["plot", 'AOT_440_std_dev:' + os.path.join(data_directory, 'Abracos_Hill_AOT_6_hourly.nc'),
                     valid_aeronet_variable + ":" + another_valid_aeronet_filename]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    @raises(InvalidDimensionError)
    def test_multiple_time_series_incompatible_axes_scatter(self):
        # JASCIS-231
        output_file_opt = ["--output", self.id() + ".png"]
        opts = ['--type=scatter']

        # The aggregated data has some guessed axis labels (x and y are lon and lat respectively) which don't
        #  correspond to the other aeronet file, so this should be caught and related to the user.
        arguments = ["plot", 'AOT_440_std_dev:' + os.path.join(data_directory, 'Abracos_Hill_AOT_6_hourly.nc'),
                     valid_aeronet_variable + ":" + another_valid_aeronet_filename]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    def test_multiple_time_series_default_axes_files_with_named_xaxis(self):
        # JASCIS-231
        output_file_opt = ["--output", self.id() + ".png"]
        opts = ['--xaxis=time']

        arguments = ["plot", 'AOT_440_std_dev:' + os.path.join(data_directory, 'Abracos_Hill_AOT_6_hourly.nc'),
                     valid_aeronet_variable + ":" + another_valid_aeronet_filename]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()

    @raises(ProductPluginException)
    def test_aeronet_multiple_variable_plots(self):
        output_file_opt = ["--output", self.id() + ".png"]
        opts = []

        # Plotting doesn't support multiple variables
        arguments = ["plot", "AOT_532,AOT_551" + ":" + valid_aeronet_filename]

        main_arguments = parse_args(arguments + opts + output_file_opt)
        plot_cmd(main_arguments)

        self.check_graphic()