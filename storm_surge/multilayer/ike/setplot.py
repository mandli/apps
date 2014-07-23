
""" 
Set up the plot figures, axes, and items to be done for each frame.

This module is imported by the plotting routines and then the
function setplot is called to set the plot parameters.
    
"""

article = False

import os

import numpy
import scipy.io

# Plot customization
import matplotlib

# Use LaTeX for all text
matplotlib.rcParams['text.usetex'] = True

# Markers and line widths
matplotlib.rcParams['lines.linewidth'] = 2.0
matplotlib.rcParams['lines.markersize'] = 6
matplotlib.rcParams['lines.markersize'] = 8

# Font Sizes
matplotlib.rcParams['font.size'] = 16
matplotlib.rcParams['axes.labelsize'] = 16
matplotlib.rcParams['legend.fontsize'] = 12
matplotlib.rcParams['xtick.labelsize'] = 16
matplotlib.rcParams['ytick.labelsize'] = 16

# DPI of output images
if article:
    matplotlib.rcParams['savefig.dpi'] = 300
else:
    matplotlib.rcParams['savefig.dpi'] = 100

import matplotlib.pyplot as plt
import datetime

# from clawpack.visclaw import colormaps
import clawpack.clawutil.data as clawutil
import clawpack.amrclaw.data as amrclaw
import clawpack.geoclaw.data as geodata

import clawpack.geoclaw.surge.plot as surge
import clawpack.geoclaw.surge.data
import clawpack.geoclaw.multilayer.plot as multilayer
import clawpack.geoclaw.multilayer.data

try:
    from setplotfg import setplotfg
except:
    setplotfg = None

# Gauge support
days2seconds = lambda days: days * 60.0**2 * 24.0
date2seconds = lambda date: days2seconds(date.days) + date.seconds
seconds2days = lambda secs: secs / (24.0 * 60.0**2)
min2deg = lambda minutes: minutes / 60.0
ft2m = lambda x:0.3048 * x
def read_tide_gauge_data(base_path, skiprows=5, verbose=False):
    r"""Read the gauge info data file.

    Returns a dictionary for each gauge in the table.
      Keys: 'location': (tuple), 'depth': float, 'gauge_no': int
            'mean_water': (ndarray), 't': (ndarray)

    """
    stations = {}
    station_info_file = open(os.path.join(base_path,'Ike_Gauges_web.txt'),'r')

    # Skip past header
    for i in xrange(skiprows):
        station_info_file.readline()

    # Read in each station
    for line in station_info_file:
        data_line = line.split()
        if data_line[6] == "OK":
            stations[data_line[0]] = {
                    'location':[float(data_line[4]) + min2deg(float(data_line[5])),
                                float(data_line[2]) + min2deg(float(data_line[3]))],
                         'depth':float(data_line[8]) + float(data_line[9]),
                      'gauge_no':0}
            if data_line[1] == '-':
                stations[data_line[0]]['gauge_no'] = ord(data_line[0])
            else:
                stations[data_line[0]]['gauge_no'] = int(data_line[1])
            if verbose:
                print "Station %s: %s" % (data_line[0],stations[data_line[0]])
            
            # Load and extract real station data
            data = scipy.io.loadmat(os.path.join(base_path,'result_%s.mat' % data_line[0]))
            stations[data_line[0]]['t'] = data['yd_processed'][0,:]
            stations[data_line[0]]['mean_water'] = data['mean_water'].transpose()[0,:]

    station_info_file.close()

    return stations


def read_adcirc_gauge_data(only_gauges=None, base_path="", verbose=False):
    r""""""

    if only_gauges is None:
        gauge_list = [120, 121, 122, 123]
    else:
        gauge_list = only_gauges

    gauge_file_list = [os.path.join(base_path, "stat%s.dat" % str(i).zfill(4)) 
                 for i in gauge_list]

    stations = {}
    for (i,gauge_file) in enumerate(gauge_file_list):
        data = numpy.loadtxt(gauge_file)
        stations[i+1] = data
        if verbose:
            print "Read in ADCIRC gauge file %s" % gauge_file

    return stations

# Gauge name translation
gauge_name_trans = {1:"W", 2:"X", 3:"Y", 4:"Z"}
gauge_surface_offset = [0.0, 0.0]
gauge_landfall = []
gauge_landfall.append(datetime.datetime(2008,9,13 + 1,7) 
                                            - datetime.datetime(2008,1,1,0))
gauge_landfall.append(datetime.datetime(2008,9,13 - 1,7) 
                                            - datetime.datetime(2008,1,1,0))
gauge_landfall.append(days2seconds(4.25))

# Read in Kennedy et al Gauges
base_path = os.path.expandvars("$CLAW/apps/storm_surge/gulf/ike/")
kennedy_gauge_path = os.path.join(base_path,'gauge_data')
kennedy_gauges = read_tide_gauge_data(kennedy_gauge_path)
keys = kennedy_gauges.keys()
for gauge_label in keys:
    if kennedy_gauges[gauge_label]['gauge_no'] not in [1, 2, 3, 4]:
        kennedy_gauges.pop(gauge_label)
gauge_list = [gauge['gauge_no'] for gauge in kennedy_gauges.itervalues()]

# Read in ADCIRC gauges
adcirc_path = os.path.join(base_path,"gauge_data")
ADCIRC_gauges = read_adcirc_gauge_data(base_path=os.path.join(adcirc_path,'new_data'))


def setplot(plotdata):
    r"""Setplot function for surge plotting"""
    

    plotdata.clearfigures()  # clear any old figures,axes,items data
    plotdata.format = 'binary'

    fig_num_counter = surge.figure_counter()

    # Load data from output
    clawdata = clawutil.ClawInputData(2)
    clawdata.read(os.path.join(plotdata.outdir,'claw.data'))
    amrdata = amrclaw.AmrclawInputData(clawdata)
    amrdata.read(os.path.join(plotdata.outdir,'amr.data'))
    physics = geodata.GeoClawData()
    physics.read(os.path.join(plotdata.outdir,'geoclaw.data'))
    surge_data = clawpack.geoclaw.surge.data.SurgeData()
    surge_data.read(os.path.join(plotdata.outdir,'surge.data'))
    friction_data = clawpack.geoclaw.surge.data.FrictionData()
    friction_data.read(os.path.join(plotdata.outdir,'friction.data'))
    multilayer_data = clawpack.geoclaw.multilayer.data.MultilayerData()
    multilayer_data.read(os.path.join(plotdata.outdir,'multilayer.data'))

    # Load storm track
    track = surge.track_data(os.path.join(plotdata.outdir,'fort.track'))

    # Calculate landfall time, off by a day, maybe leap year issue?
    landfall_dt = datetime.datetime(2008,9,13,7) - datetime.datetime(2008,1,1,0)
    landfall = (landfall_dt.days - 1.0) * 24.0 * 60**2 + landfall_dt.seconds

    # Set afteraxes function
    surge_afteraxes = lambda cd: surge.surge_afteraxes(cd, 
                                        track, landfall, plot_direction=False)

    # Plot limits and labels
    surface_range = 5.0
    speed_range = 3.0
    eta = multilayer_data.eta

    surface_limits = [[eta[0] - surface_range, eta[0] + surface_range], 
                      [eta[1] - surface_range, eta[1] + surface_range]]
    surface_contours = [[-5,-4.5,-4,-3.5,-3,-2.5,-2,-1.5,-1,-0.5,
                                    0.5,1,1.5,2,2.5,3,3.5,4,4.5,5],
                        [contour + eta[1] for contour in 
                                    [-5,-4.5,-4,-3.5,-3,-2.5,-2,-1.5,-1,-0.5,
                                     0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]]]
    surface_ticks = [[-5,-4,-3,-2,-1,0,1,2,3,4,5], 
                     [tick + eta[1] for tick in (-5,-4,-3,-2,-1,0,1,2,3,4,5)]]
    surface_labels = [[str(value) for value in surface_ticks[0]],
                      [str(value) for value in surface_ticks[1]]]
    speed_limits = [[0.0, speed_range], [0.0,speed_range]]
    speed_contours = [numpy.linspace(0.0,speed_range,13), 
                      numpy.linspace(0.0,speed_range,13)]
    speed_ticks = [[0,1,2,3], [0,1,2,3]]
    speed_labels = [[str(value) for value in speed_ticks[0]], 
                    [str(value) for value in speed_ticks[1]]]
    depth_limits = [[0.0, 200.0], [0.0, 500]]

    wind_limits = [0, 64]
    pressure_limits = [935, 1013]
    friction_bounds = [0.01, 0.04]
    land_limits = [eta[1], 10.0]

    # def pcolor_afteraxes(current_data):
    #     surge_afteraxes(current_data)
    #     surge.gauge_locations(current_data,gaugenos=[6])
    
    def contour_afteraxes(current_data):
        surge_afteraxes(current_data)

    def add_custom_colorbar_ticks_to_axes(axes, item_name, ticks, tick_labels=None):
        axes.plotitem_dict[item_name].colorbar_ticks = ticks
        axes.plotitem_dict[item_name].colorbar_tick_labels = tick_labels

    # ==========================================================================
    # ==========================================================================
    #   Plot specifications
    # ==========================================================================
    # ==========================================================================
    axes_titles = ['Top', 'Bottom']

    def gulf_after_axes(cd):
        if article:
            plt.subplots_adjust(left=0.08, bottom=0.04, right=0.97, top=0.96)
        else:
            plt.subplots_adjust(left=0.05, bottom=0.07, right=1.00, top=0.93)
        surge_afteraxes(cd)

    def latex_after_axes(cd):
        if article:
            plt.subplots_adjust(left=0.07, bottom=0.14, right=1.0, top=0.86)
        # else:
            # plt.subplots_adjust(right=1.0)
        surge_afteraxes(cd)

    # Plot settings dict
    plot_settings = {"Gulf":{"limits":[[clawdata.lower[0], clawdata.upper[0]],
                                       [clawdata.lower[1], clawdata.upper[1]]], 
                             "shrink":0.9,
                             "afteraxes":gulf_after_axes}}#,
                     # "LaTex Shelf":{"limits":[[-97.5,-88.5], [27.5,30.5]], 
                     #                "shrink":1.0,
                     #                "afteraxes":latex_after_axes} }


    # =====================
    #  Surfaces and Depths
    # =====================
    for (region, settings) in plot_settings.iteritems():

        surf_figure = plotdata.new_plotfigure(name='Surfaces - %s' % region,
                                             figno=fig_num_counter.get_counter())
        surf_figure.show = True
        surf_figure.kwargs = {'figsize':(7 * multilayer_data.num_layers,4)}

        depth_figure = plotdata.new_plotfigure(name='Depths - %s' % region,
                                             figno=fig_num_counter.get_counter())
        depth_figure.show = True
        depth_figure.kwargs = {'figsize':(7 * multilayer_data.num_layers,4)}

        speed_figure = plotdata.new_plotfigure(name='Speed - %s' % region,
                                             figno=fig_num_counter.get_counter())
        speed_figure.show = True
        speed_figure.kwargs = {'figsize':(7 * multilayer_data.num_layers,4)}


        # Test
        test_figure = plotdata.new_plotfigure(name='Test - %s' % region,
                                             figno=fig_num_counter.get_counter())
        test_figure.show = True
        test_figure.kwargs = {'figsize':(7 * multilayer_data.num_layers,4)}

        for layer in xrange(1, multilayer_data.num_layers + 1):
            
            # Test
            plotaxes = test_figure.new_plotaxes()
            plotaxes.scaled = True
            plotaxes.xlimits = settings['limits'][0]
            plotaxes.ylimits = settings['limits'][1]
            plotaxes.afteraxes = settings['afteraxes']
            plotaxes.axescmd = "subplot(1,%s,%s)" % (multilayer_data.num_layers,
                                                     layer)

            multilayer.add_bathy(plotaxes, plot_type="contour", 
                                           contour_levels=multilayer_data.eta[layer-1])
            # multilayer.add_land(plotaxes, layer=layer, plot_var)
            # plotaxes.plotitem_dict['depth_%s' % (layer)].add_colorbar = True
            # plotaxes.plotitem_dict['bathy'].amr_patchedges_show = [0,0,0,0,0,0,0]

            # Surfaces
            plotaxes = surf_figure.new_plotaxes()
            plotaxes.title = '%s Surface' % axes_titles[layer - 1]
            plotaxes.axescmd = "subplot(1,%s,%s)" % (multilayer_data.num_layers,
                                                     layer)
            plotaxes.scaled = True
            plotaxes.xlimits = settings['limits'][0]
            plotaxes.ylimits = settings['limits'][1]
            plotaxes.afteraxes = settings['afteraxes']

            multilayer.add_surface_elevation(plotaxes, layer, 
                                            plot_type='pcolor',
                                            bounds=surface_limits[layer - 1],
                                            shrink=settings['shrink'])
                                            # contours=surface_contours[layer - 1],
            multilayer.add_land(plotaxes, layer, topo_min=land_limits[0], 
                                                 topo_max=land_limits[1])
            plotaxes.plotitem_dict['surface_%s' % (layer)].amr_patchedges_show = [0,0,0,0,0,0,0]
            plotaxes.plotitem_dict['land_%s' % (layer)].amr_patchedges_show = [0,0,0,0,0,0,0]
            if article:
                plotaxes.plotitem_dict['surface_%s' % (layer)].add_colorbar = False
            else:
                add_custom_colorbar_ticks_to_axes(plotaxes, 
                                                  'surface_%s' % layer, 
                                                  surface_ticks[layer - 1], 
                                                  surface_labels[layer - 1])

            # Depths
            plotaxes = depth_figure.new_plotaxes()
            plotaxes.title = '%s Depth' % axes_titles[layer - 1]
            plotaxes.axescmd = "subplot(1,%s,%s)" % (multilayer_data.num_layers,
                                                     layer)
            plotaxes.scaled = True
            plotaxes.xlimits = settings['limits'][0]
            plotaxes.ylimits = settings['limits'][1]
            plotaxes.afteraxes = settings['afteraxes']

            multilayer.add_depth(plotaxes, layer, plot_type='pcolor',
                                            shrink=settings['shrink'],
                                            bounds=depth_limits[layer - 1])
                                            
            multilayer.add_land(plotaxes, layer)
            plotaxes.plotitem_dict['depth_%s' % (layer)].amr_patchedges_show = [0]
            if layer == 2:
                # multilayer.add_bathy_contours(plotaxes, color='r')
                multilayer.add_bathy(plotaxes, plot_type='contour', color='r')
                # plotaxes.plotitem_dict['bathy_contours_1'].amr_contour_show = [1]
            # if article:
                # plotaxes.plotitem_dict['depth_%s' % (layer + 1)].add_colorbar = False
            # else:
                # add_custom_colorbar_ticks_to_axes(plotaxes, 'depth_%s' % (layer+1), depth_ticks[layer], depth_labels[layer])

            # Speed
            plotaxes = speed_figure.new_plotaxes()
            plotaxes.title = "%s Currents" % axes_titles[layer - 1]
            plotaxes.axescmd = "subplot(1,%s,%s)" % (multilayer_data.num_layers,
                                                     layer)
            plotaxes.scaled = True
            plotaxes.xlimits = settings['limits'][0]
            plotaxes.ylimits = settings['limits'][1]
            plotaxes.afteraxes = settings['afteraxes']


            multilayer.add_speed(plotaxes, layer, plot_type='contourf', 
                                               contours=speed_contours[layer-1], 
                                               shrink=settings['shrink'])
            if article:
                plotaxes.plotitem_dict['speed_%s' % (layer)].add_colorbar = False
            else:
                add_custom_colorbar_ticks_to_axes(plotaxes, 'speed_%s' % layer, 
                                                  speed_ticks[layer-1],
                                                  speed_labels[layer-1])

            multilayer.add_land(plotaxes, layer)
            plotaxes.plotitem_dict['speed_%s' % (layer)].amr_patchedges_show = [0,0,0,0,0,0,0]
            plotaxes.plotitem_dict['land_%s' % (layer)].amr_patchedges_show = [0,0,0,0,0,0,0]


    #
    # Friction field
    #
    plotfigure = plotdata.new_plotfigure(name='Friction',
                                         figno=fig_num_counter.get_counter())
    plotfigure.show = friction_data.variable_friction and True

    def friction_after_axes(cd):
        plt.subplots_adjust(left=0.08, bottom=0.04, right=0.97, top=0.96)
        plt.title(r"Manning's $n$ Coefficient")
        surge_afteraxes(cd)

    plotaxes = plotfigure.new_plotaxes()
    plotaxes.xlimits = plot_settings["Gulf"]["limits"][0]
    plotaxes.ylimits = plot_settings["Gulf"]["limits"][1]
    plotaxes.title = "Manning's N Coefficient"
    plotaxes.afteraxes = friction_after_axes
    plotaxes.scaled = True

    surge.add_friction(plotaxes, bounds=friction_bounds, shrink=0.9)
    plotaxes.plotitem_dict['friction'].amr_patchedges_show = [0,0,0,0,0,0,0]
    plotaxes.plotitem_dict['friction'].colorbar_label = "$n$"

    # ==========================
    #  Hurricane Forcing fields
    # ==========================
    
    # Pressure field
    plotfigure = plotdata.new_plotfigure(name='Pressure',  
                                         figno=fig_num_counter.get_counter())
    plotfigure.show = surge_data.pressure_forcing and True
    
    plotaxes = plotfigure.new_plotaxes()
    plotaxes.xlimits = plot_settings["Gulf"]["limits"][0]
    plotaxes.ylimits = plot_settings["Gulf"]["limits"][1]
    plotaxes.title = "Pressure Field"
    plotaxes.afteraxes = gulf_after_axes
    plotaxes.scaled = True
    
    surge.add_pressure(plotaxes, bounds=pressure_limits, 
                                 shrink=plot_settings['Gulf']['shrink'])
    plotaxes.plotitem_dict['pressure'].amr_patchedges_show = [0,0,0,0,0,0,0,0]
    multilayer.add_land(plotaxes, layer=1)
    
    # Wind field
    plotfigure = plotdata.new_plotfigure(name='Wind Speed', 
                                         figno=fig_num_counter.get_counter())
    plotfigure.show = surge_data.wind_forcing and True
    
    plotaxes = plotfigure.new_plotaxes()
    plotaxes.xlimits = plot_settings["Gulf"]["limits"][0]
    plotaxes.ylimits = plot_settings["Gulf"]["limits"][1]
    plotaxes.title = "Wind Field"
    plotaxes.afteraxes = gulf_after_axes
    plotaxes.scaled = True
    
    surge.add_wind(plotaxes, bounds=wind_limits, plot_type='pcolor',
                             shrink=plot_settings['Gulf']['shrink'])
    plotaxes.plotitem_dict['wind'].amr_patchedges_show = [0,0,0,0,0,0,0,0]
    multilayer.add_land(plotaxes, layer=1)

    # ========================================================================
    #  Figures for gauges
    # ========================================================================
    plotfigure = plotdata.new_plotfigure(name='Surface & topo', figno=300, \
                    type='each_gauge')
    plotfigure.show = True
    plotfigure.clf_each_gauge = True
    # plotfigure.kwargs['figsize'] = (16,10)

    def gauge_after_axes(cd):

        if cd.gaugeno in [1,2,3,4]:
            axes = plt.gca()
            # Add Kennedy gauge data
            kennedy_gauge = kennedy_gauges[gauge_name_trans[cd.gaugeno]]
            axes.plot(kennedy_gauge['t'] - seconds2days(date2seconds(gauge_landfall[0])), 
                     kennedy_gauge['mean_water'] + kennedy_gauge['depth'], 'k-', 
                     label='Gauge Data')

            # Add GeoClaw gauge data
            geoclaw_gauge = cd.gaugesoln
            axes.plot(seconds2days(geoclaw_gauge.t - date2seconds(gauge_landfall[1])),
                  geoclaw_gauge.q[3,:] + gauge_surface_offset[0], 'b--', 
                  label="GeoClaw")

            # Add ADCIRC gauge data
            ADCIRC_gauge = ADCIRC_gauges[kennedy_gauge['gauge_no']]
            axes.plot(seconds2days(ADCIRC_gauge[:,0] - gauge_landfall[2]), 
                     ADCIRC_gauge[:,1] + gauge_surface_offset[1], 'r-.', label="ADCIRC")

            # Fix up plot
            axes.set_title('Station %s' % cd.gaugeno)
            axes.set_xlabel('Days relative to landfall')
            axes.set_ylabel('Surface (m)')
            axes.set_xlim([-2,1])
            axes.set_ylim([-1,5])
            axes.set_xticks([-2,-1,0,1])
            axes.set_xticklabels([r"$-2$",r"$-1$",r"$0$",r"$1$"])
            axes.grid(True)
            axes.legend()

            plt.hold(False)

        surge.gauge_afteraxes(cd)


    # Set up for axes in this figure:
    plotaxes = plotfigure.new_plotaxes()
    plotaxes.xlimits = [-2,1]
    # plotaxes.xlabel = "Days from landfall"
    # plotaxes.ylabel = "Surface (m)"
    plotaxes.ylimits = [-1,5]
    plotaxes.title = 'Surface'
    plotaxes.afteraxes = gauge_after_axes

    # Plot surface as blue curve:
    plotitem = plotaxes.new_plotitem(plot_type='1d_plot')
    plotitem.plot_var = 3
    plotitem.plotstyle = 'b-'

    # =====================
    #  Gauge Location Plot
    # =====================
    # gauge_xlimits = [-95.5, -94]
    # gauge_ylimits = [29.0, 30.0]
    # gauge_location_shrink = 0.75
    # def gauge_after_axes(cd):
    #     plt.subplots_adjust(left=0.12, bottom=0.06, right=0.97, top=0.97)
    #     surge_afteraxes(cd)
    #     surge.gauge_locations(cd, gaugenos=[1, 2, 3, 4])
    #     plt.title("Gauge Locations")

    # plotfigure = plotdata.new_plotfigure(name='Gauge Locations',  
    #                                      figno=fig_num_counter.get_counter())
    # plotfigure.show = True

    # # Set up for axes in this figure:
    # plotaxes = plotfigure.new_plotaxes()
    # plotaxes.title = 'Surface'
    # plotaxes.scaled = True
    # plotaxes.xlimits = gauge_xlimits
    # plotaxes.ylimits = gauge_ylimits
    # plotaxes.afteraxes = gauge_after_axes
    
    # surge.add_surface_elevation(plotaxes, plot_type='contourf', 
    #                                            contours=surface_contours,
    #                                            shrink=gauge_location_shrink)
    # # surge.add_surface_elevation(plotaxes, plot_type="contourf")
    # add_custom_colorbar_ticks_to_axes(plotaxes, 'surface', surface_ticks, surface_labels)
    # surge.add_land(plotaxes)
    # # plotaxes.plotitem_dict['surface'].amr_patchedges_show = [0,0,0,0,0,0,0]
    # # plotaxes.plotitem_dict['surface'].add_colorbar = False
    # # plotaxes.plotitem_dict['surface'].pcolor_cmap = plt.get_cmap('jet')
    # # plotaxes.plotitem_dict['surface'].pcolor_cmap = plt.get_cmap('gist_yarg')
    # # plotaxes.plotitem_dict['surface'].pcolor_cmin = 0.0
    # # plotaxes.plotitem_dict['surface'].pcolor_cmax = 5.0
    # plotaxes.plotitem_dict['surface'].amr_patchedges_show = [0,0,0,0,0,0,0]
    # plotaxes.plotitem_dict['land'].amr_patchedges_show = [0,0,0,0,0,0,0]
    
    # # ==============================================================
    # #  Debugging Plots, only really work if using interactive plots
    # # ==============================================================
    # #
    # # Water Velocity Components
    # #
    # plotfigure = plotdata.new_plotfigure(name='Velocity Components - Entire Domain',  
    #                                      figno=fig_num_counter.get_counter())
    # plotfigure.show = False

    # # X-Component
    # plotaxes = plotfigure.new_plotaxes()
    # plotaxes.axescmd = "subplot(121)"
    # plotaxes.title = 'Velocity, X-Component'
    # plotaxes.scaled = True
    # plotaxes.xlimits = gulf_xlimits
    # plotaxes.ylimits = gulf_ylimits
    # plotaxes.afteraxes = gulf_after_axes

    # plotitem = plotaxes.new_plotitem(plot_type='2d_pcolor')
    # plotitem.plot_var = surge.water_u
    # plotitem.pcolor_cmap = colormaps.make_colormap({1.0:'r',0.5:'w',0.0:'b'})
    # plotitem.pcolor_cmin = -speed_limits[1]
    # plotitem.pcolor_cmax = speed_limits[1]
    # plotitem.colorbar_shrink = gulf_shrink
    # plotitem.add_colorbar = True
    # plotitem.amr_celledges_show = [0,0,0]
    # plotitem.amr_patchedges_show = [1,1,1]

    # surge.add_land(plotaxes)

    # # Y-Component
    # plotaxes = plotfigure.new_plotaxes()
    # plotaxes.axescmd = "subplot(122)"
    # plotaxes.title = 'Velocity, Y-Component'
    # plotaxes.scaled = True
    # plotaxes.xlimits = gulf_xlimits
    # plotaxes.ylimits = gulf_ylimits
    # plotaxes.afteraxes = gulf_after_axes

    # plotitem = plotaxes.new_plotitem(plot_type='2d_pcolor')
    # plotitem.plot_var = surge.water_v
    # plotitem.pcolor_cmap = colormaps.make_colormap({1.0:'r',0.5:'w',0.0:'b'})
    # plotitem.pcolor_cmin = -speed_limits[1]
    # plotitem.pcolor_cmax = speed_limits[1]
    # plotitem.colorbar_shrink = gulf_shrink
    # plotitem.add_colorbar = True
    # plotitem.amr_celledges_show = [0,0,0]
    # plotitem.amr_patchedges_show = [1,1,1]
    
    # surge.add_land(plotaxes)


    #-----------------------------------------

    # Parameters used only when creating html and/or latex hardcopy
    # e.g., via pyclaw.plotters.frametools.printframes:

    if article:
        plotdata.printfigs = True                # print figures
        plotdata.print_format = 'png'            # file format
        plotdata.print_framenos = [54,60,66,72,78,84]            # list of frames to print
        plotdata.print_gaugenos = [1,2,3,4]          # list of gauges to print
        plotdata.print_fignos = [4,5,6,7,10,3,300]            # list of figures to print
        plotdata.html = True                     # create html files of plots?
        plotdata.html_homelink = '../README.html'   # pointer for top of index
        plotdata.latex = False                    # create latex file of plots?
        plotdata.latex_figsperline = 2           # layout of plots
        plotdata.latex_framesperline = 1         # layout of plots
        plotdata.latex_makepdf = False           # also run pdflatex?

    else:
        plotdata.printfigs = True                # print figures
        plotdata.print_format = 'png'            # file format
        plotdata.print_framenos = 'all'            # list of frames to print
        plotdata.print_gaugenos = [1,2,3,4]          # list of gauges to print
        plotdata.print_fignos = 'all'            # list of figures to print
        plotdata.html = True                     # create html files of plots?
        plotdata.html_homelink = '../README.html'   # pointer for top of index
        plotdata.latex = True                    # create latex file of plots?
        plotdata.latex_figsperline = 2           # layout of plots
        plotdata.latex_framesperline = 1         # layout of plots
        plotdata.latex_makepdf = False           # also run pdflatex?

    return plotdata

