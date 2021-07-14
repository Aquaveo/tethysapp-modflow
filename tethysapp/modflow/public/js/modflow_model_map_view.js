/*****************************************************************************
 * FILE:    modflow_model_map_view.js
 * DATE:    February 6, 2019
 * AUTHOR:  Corey Krewson
 * COPYRIGHT: (c) Aquaveo 2019
 * LICENSE:
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

var MODFLOW_MODEL_MAP_VIEW = (function() {
	// Wrap the library in a package function
	"use strict"; // And enable strict mode for this library

	/************************************************************************
 	*                      MODULE LEVEL / GLOBAL VARIABLES
 	*************************************************************************/
 	// Constants

 	// Module variables
 	var m_public_interface;				// Object returned by the module

 	var m_map,                          // OpenLayers map object
        m_layers;                       // OpenLayers layer objects mapped to by layer by layer_name

	/************************************************************************
 	*                    PRIVATE FUNCTION DECLARATIONS
 	*************************************************************************/
 	// Config
 	var setup_modpath_select, get_csrf_token, group_layers_and_sp, result_group_layers_and_sp;

 	// Model Publication Link
 	var init_model_publication_link;

 	// Create Tool Tab
 	var init_tools_tab;

 	// Create Tool Tab
 	var init_results_tab;

 	// Flow Path Slide Sheet
 	var init_slide_sheet, bind_flow_path_buttons, load_flow_path, show_flow_path;

 	// Pump Impact Slide Sheet
 	var bind_pump_impact_buttons, load_pump_impact, show_pump_impact, add_pump_impact_row, delete_row_pump_impact,
 	location_pump_impact, run_pump_impact_tool, create_point_from_latlon, bind_pump_impact_checkbox,
 	create_pump_impact_legends, init_well_upload, bind_cancel_modpath_button, create_drawdown_legends;

    // General Map Interation
    var add_map_interaction, remove_map_interaction, draw, snap;

    // Flow Path Map Interation
    var init_flow_path_creation, remove_temporary_layers, flow_path_listener;

    // Alerts
    var bind_alert_close, show_alert, init_modal_pagination, bind_help_modal_check;

    // Layer Controls
    var init_layer_name_change, init_remove_layer, init_public_toggle;

    // Stream Depletion Tool
    var stream_sol_group_name, stream_sol_group_id, stream_sol_percentage_group_name, stream_sol_percentage_group_id,
        streamflow_uuid, streamleakage_uuid, streamflow_sol_name, streamleakage_sol_name,
        streamleakage_percentage_sol_name, streamflow_percentage_sol_name, streamflow_percentage_uuid,
        streamleakage_percentage_uuid;

    // Drawdown Tool
    var drawdown_sol_group_name, drawdown_sol_group_id, drawdown_uuid, drawdown_sol_name;

    // Particle Tracking Tool
    var particle_sol_group_name, particle_sol_group_id, particle_uuid, particle_sol_name, particle_layers, particle_count;

    // Help Modal
    var init_help_modal;

    // Utility Functions
    var clear_layer_name, show_modpath_tool, show_pump_impact_tool, remove_feature, slide_sheet_close_event,
    show_legend, update_unit, cancel_job, check_point_inside, check_well_depth, generate_uuid;

    // Legend-Layer Data structure
    var init_legend_layer_data, legend_layer_data, init_solution_legend_display;

    // Layers and Stress Periods
    var layer_group_list, stress_period_group_list, no_layer_group_list, bind_selector, data_selection;

    // Constant
    var m_$data_popup_container = $('#spatial-data-popup');
    var m_$data_popup_content = $('#spatial-data-form');
    var m_$data_popup_closer = $('#spatial-data-popup-close-btn');
    var well_input_name = "DiversionInput";

 	/************************************************************************
 	*                    PRIVATE FUNCTION IMPLEMENTATIONS
 	*************************************************************************/
    // Config

    setup_modpath_select = function() {
        // Get handle on map
	    m_map = TETHYS_MAP_VIEW.getMap();

	    // Setup layer map
	    m_layers = {};

	    // Get id from tethys_data attribute
	    m_map.getLayers().forEach(function(item, index, array) {
	        if ('tethys_data' in item && 'layer_id' in item.tethys_data) {
	           if (item.tethys_data.layer_name in m_layers) {
	               console.log('Warning: layer_id already in layers map: "' + item.tethys_data.layer_id + '".');
	           }
	           m_layers[item.tethys_data.layer_id] = item;
	        }
	    });
    };

    group_layers_and_sp = function() {
        let layer_tab_panel = $('#layers-tab-panel, #results-tab-panel');
        let layer_groups = layer_tab_panel.find('.layer-group-item')
        let i;
        let check_status;
        stress_period_group_list = new Array();
        layer_group_list = new Array();
        no_layer_group_list = new Array();
        $.each(layer_groups, function(index, content) {
            // Get all layers in this group
            if (content.id) {
                let layer_list_id = $('#' + content.id).next()[0].id
                if (layer_list_id) {
                    let layer_lists =  $('#' + layer_list_id).children()
                    $.each(layer_lists, function(layer_index, layer_content) {
                        let layer_id = layer_content.getElementsByClassName('layer-visibility-control')[0].dataset.layerId;
                        // If last 3 is number and the 4th to last char is not _, it's the stress period
                        let layer_id_stress_period = layer_id.substring(layer_id.length -3, layer_id.length);
                        if (!isNaN(Number(layer_id_stress_period))) {
                            let stress_period = Number(layer_id_stress_period)
                            if (layer_id.substring(layer_id.length -4, layer_id.length -3) != "_") {
                                if (stress_period_group_list[stress_period]) {
                                    stress_period_group_list[stress_period].push(layer_id);
                                }
                                else {
                                    stress_period_group_list[stress_period]= new Array(layer_id);
                                }
                            }
                            else if (layer_id.includes('RCH')) {
                                if (no_layer_group_list[stress_period]) {
                                    no_layer_group_list[stress_period].push(layer_id);
                                }
                                else {
                                    no_layer_group_list[stress_period]= new Array(layer_id);
                                }
                            }

                        }
                        let layer_id_layer_number = ''
                        // If 6th to 3th from the right of the string is number, it's the layer number
                        if (layer_id.substring(layer_id.length -4, layer_id.length -3) == "_") {
                            if (!layer_id.includes('RCH')) {
                                layer_id_layer_number = layer_id.substring(layer_id.length -3, layer_id.length)
                            }
                        }
                        else {
                            layer_id_layer_number = layer_id.substring(layer_id.length -6, layer_id.length -3)
                        }

                        if (!isNaN(Number(layer_id_layer_number))) {
                            let layer_number = Number(layer_id_layer_number)
                            if (layer_group_list[layer_number]) {
                                layer_group_list[layer_number].push(layer_id);
                            }
                            else {
                                layer_group_list[layer_number]= new Array(layer_id);
                            }
                        }
                    })
                }
            }
        });

        // Only turn on layer 1 and stress period 1 by default
        data_selection(1, 1);
    }

    init_modal_pagination = function() {
        $(document).on('click', '.page-link', function(e) {
            e.preventDefault();
            $(".page-item").removeClass("active")
            $("#help-modal .modal-body").addClass("hidden")
            $(this).parent().addClass("active")
            $('#' + $(this).data('page')).removeClass('hidden')
            console.log($(this).html());
        });
    }

    init_help_modal = function() {
        let show_helper = $('#show_helper_status').data('value')
        if (show_helper == 'True') {
            $('#help-modal').modal('show');
        }
    }

    init_legend_layer_data = function() {
        legend_layer_data = {}
        legend_layer_data['flowpath'] = []
    }

    bind_selector = function () {
        $('#layer_selector, #sp_selector').change(function() {
            let selected_layer = $('#layer_selector')[0].value;
            let selected_sp = $('#sp_selector')[0].value;
            data_selection(selected_layer, selected_sp);
        })
    }

    bind_alert_close = function () {
        $(document).on('click', '.alert .close', function(e) {
            $(this).parent().hide();
        });
    }

    bind_help_modal_check = function () {
        $('#modal-show-again').change(function() {
            // Update django session.
            var csrf_token = get_csrf_token();
            $.ajax({
                type: 'get',
                url: '/apps/modflow/update-help-modal-status/',
                data: {'status': !this.checked,
                       'page_name': 'modflow_model'},
                beforeSend: xhr => {
                    xhr.setRequestHeader('X-CSRFToken', csrf_token);
                },
            }).done(function (json) {
                if(json.success) {
                }


            })
        })
    }

    show_alert = function (message) {
        if (message) {
//            $('#modal-alert-message').html(message)
            $('#show-alert-modal').modal('show');
            $('#modal-alert-message').html(message);
        }
        $("#show-alert-ok").on('click', function() {
            $('#show-alert-modal').modal('hide');
        })
    }

    // Model Publication
    init_model_publication_link = function() {
        var publication;
        var publication_link;
        var content;
        publication = $('#publication_name').data('value')
        publication_link = $('#publication_link').data('value')
        if (!publication_link.includes('http')) {
            publication_link = 'http://' + publication_link;
        }
        if (publication_link.length > 8) {
            content = "<p>Model modified from <a href='" + publication_link + "' target='_blank'>" + publication + "</a></p>";
        }
        else {
            content = "<p></p>";
        }
        $('#nav-header').after(content);
    }

    // Create Tool Tab
    init_tools_tab = function () {
        var tools_tab_name;
        var well_influence_tool_name;
        var flow_path_tool_name;
        var content;
        var tools_content;
        tools_tab_name = $('#tools_tab_name').data('value')
        well_influence_tool_name = $('#well_influence_tool_name').data('value')
        flow_path_tool_name = $('#flow_path_tool_name').data('value')
        content = "<li role='presentation' class='active'>"
        content += "<a id='tools-tab-toggle' href='#tools-tab-panel' aria-controls='tools-tab-panel' aria-selected='true' role='tab' data-toggle='tab'>" + tools_tab_name + "</a></li>"
        $('.atcore-nav-tabs > .active').removeClass('active')
        $('.atcore-nav-tabs').prepend(content)

        // Create Stream Influence Tool
        tools_content = "<div class='app-action-button' title='Well Influence Tool'>"
        tools_content +=  "<a class='btn btn-default btn-pump_impact' style='margin-top: 10px; width:100%'>Simulate pumping effects on groundwater/surface water</a></div>"

        // Create Delineate Flow Path Tool
        tools_content += "<div class='app-action-button' title='Flow Path Tool'>"
        tools_content +=  "<a class='btn btn-default btn-flow_path' style='margin-top: 10px; width:100%'>Delineate groundwater flow path</a></div>"

        // Add disclaimer
//        tools_content += "<p style='margin-top: 10px'>*Disclaimer Text goes in here</p>"
        tools_content += "<p style='margin-top: 10px'></p>"

        // Append to tab panel
        var tab_content = "<div role='tabpanel' class='tab-pane active' id='tools-tab-panel'>" + tools_content + "</div>"
        $('.tab-content > .active').removeClass('active')
        $('.tab-content').prepend(tab_content)
    }

    // Create Tool Tab
    init_results_tab = function () {
        var results_tab_name;
        var content;
        var results_content;
        results_tab_name = $('#results_tab_name').data('value')
        content = "<li role='presentation' class='active'>"
        content += "<a id='results-tab-toggle' href='#results-tab-panel' aria-controls='results-tab-panel' aria-selected='true' role='tab' data-toggle='tab'>" + results_tab_name + "</a></li>"
        $('.atcore-nav-tabs > .active').removeClass('active')
        $('.atcore-nav-tabs').prepend(content)

        // Add placeholder
        results_content = "<p style='margin-top: 10px'></p>"

        // Append to tab panel
        var tab_content = "<div role='tabpanel' class='tab-pane active' id='results-tab-panel'>" + results_content + "</div>"
        $('.tab-content > .active').removeClass('active')
        $('.tab-content').prepend(tab_content)
    }

    init_well_upload = function() {
        $("#well-upload-submit").on('click', function(e){
            e.preventDefault();
            var formData = new FormData($("#well-upload-form")[0]);
            var csrf_token = get_csrf_token();
            $.ajax({
                type: 'POST',
                url: window.location.href,
                data: formData,
                processData: false,
                contentType: false,
                beforeSend: xhr => {
                    xhr.setRequestHeader('X-CSRFToken', csrf_token);
                },
            }).done(function (data) {
                if (data['success'] == true) {
                    var existing_table_rows = $("#pump_impact_table > tbody > tr")
                    for (let x = 0; x < existing_table_rows.length; x++) {
                        let row = $("#pump_impact_table > tbody").find('tr').eq(0);
                        let delete_button = row.find("td:eq(5) button")
                        delete_button.trigger('click')
                    }

                    const format = new ol.format.GeoJSON();
                    const features = format.readFeatures(data['geojson'], {
                                         defaultDataProjection: 'EPSG:4326',
                                         featureProjection:'EPSG:3857' })
                    let vector_id = 1;
                    for (let i = 0; i < features.length; i++) {
                        let coords = features[i].getGeometry().getCoordinates();
                        vector_id += i;
                        if (coords.length == 2) {
                            var coord_str = ol.proj.transform(coords, 'EPSG:3857', 'EPSG:4326');
                            coord_str = [coord_str[1], coord_str[0]];
                            var well_type = 'Point';
                        } else {
                            var coord_str = ''
                            for (let y = 0; y < coords[0].length; y++) {
                                let lonlat = ol.proj.transform(coords[0][y], 'EPSG:3857', 'EPSG:4326');
                                let lon = lonlat[0];
                                let lat = lonlat[1];
                                coord_str = coord_str + lat + ',' + lon
                                if (y != coords[0].length -1) {
                                    coord_str = coord_str + ';'
                                }
                            }
                            var well_type = 'Polygon';
                        }
                        add_pump_impact_row()
                        let row = $("#pump_impact_table > tbody").find('tr').eq(i);
                        let pump_button = row.find("td:eq(5) button")
                        let layer_name = 'vectorlayer' + vector_id;
                        row.find("td:eq(0) input").val(features[i].get('Flowrate'))
                        if ($('#transient_model').val() == 'True') {
                            row.find("td:eq(4) select").val(well_type)
                            row.find("td:eq(5) input").val(coord_str)
                            row.find("td:eq(6) input").val(features[i].get('Depth'))
                        }
                        else {
                            row.find("td:eq(2) select").val(well_type)
                            row.find("td:eq(3) input").val(coord_str)
                            row.find("td:eq(4) input").val(features[i].get('Depth'))
                        }
                        let single_feature = []
                        single_feature.push(features[i])

                        const wellLayer = new ol.layer.Vector({
                            source: new ol.source.Vector({features: single_feature}),
                            style: new ol.style.Style({
                              fill: new ol.style.Fill({
                                color: 'rgba(255, 255, 255, 0.2)'
                              }),
                              stroke: new ol.style.Stroke({
                                color: '#ff3232',
                                width: 2
                              }),
                              image: new ol.style.Circle({
                                radius: 4,
                                fill: new ol.style.Fill({
                                  color: '#ff3232'
                                })
                              })
                            })
                        })
                        wellLayer.set('name', layer_name)
                        m_map.addLayer(wellLayer)
                        pump_button.data('layer', layer_name)
                        $("#pump-upload-modal").modal("hide");
                    }
                }
            })
        });
    };

    init_public_toggle = function() {
        // Rename layer
        $('.layer-dropdown-toggle').on('switchChange.bootstrapSwitch', function(e, state) {
            let $action_button = $(e.target);
            var $layer_label = $action_button.closest('.layers-context-menu').prev();
            var group_name = $layer_label.find('.layer-visibility-control').first().attr('name')
            var custom_layer_uuid = ''
            if (!group_name) {
                var layer_name = $layer_label.find('.layer-group-visibility-control').first().data('layer-group-id')
            } else {
                var layer_name = $layer_label.find('.layer-visibility-control').first().data('layer-id')
                if (group_name == 'custom_layers') {
                    custom_layer_uuid = $layer_label.find('.layer-visibility-control').first().data('layer-variable')
                }
            }
            var csrf_token = get_csrf_token();
            $.ajax({
                    type: 'POST',
                    url: window.location.href,
                    data: {'group_name': group_name,
                           'state': state,
                           'layer_name': layer_name,
                           'layer_uuid': custom_layer_uuid,
                           'method': 'layer_public_toggle_change'},
                    beforeSend: xhr => {
                        xhr.setRequestHeader('X-CSRFToken', csrf_token);
                    },
                }).done(function (data) {

                })
            // TODO: Implement
            // TODO: Save state to workflow - store in attributes?
        });
    };

    init_layer_name_change = function() {
        $(document).on('click', '.rename-action', function(e) {
            let $action_button = $(e.target);
            var $layer_label = $action_button.closest('.layers-context-menu').prev();
            var layer_id = ''

            var group_name = $layer_label.find('.layer-visibility-control').first().attr('name')

            if (!group_name) {
                var layer_name = $layer_label.find('.layer-group-visibility-control').first().data('layer-group-id')
            } else {
                var layer_name = $layer_label.find('.layer-visibility-control').first().data('layer-id')
                if (group_name == 'custom_layers') {
                    layer_id = $layer_label.find('.layer-visibility-control').first().data('layer-id')
                }
            }
            if (!layer_name) {
                return
            }
            var csrf_token = get_csrf_token();
            $('#do-action-button').on('click', function() {
                var new_name = $("#new-name-field").val()
                $.ajax({
                    type: 'POST',
                    url: window.location.href,
                    data: {'layer_name': layer_name,
                           'group_name': group_name,
                           'new_name': new_name,
                           'layer_id': layer_id,  // for custom layers
                           'method': 'layer_name_change'},
                    beforeSend: xhr => {
                        xhr.setRequestHeader('X-CSRFToken', csrf_token);
                    },
                }).done(function (data) {

                })
            })
	    })
    };

    init_solution_legend_display = function() {
        $(document).on('change', 'input[type="checkbox"]', function(e) {
            if (e.currentTarget.checked) {
                show_legend(true, e.currentTarget.dataset.layerVariable);
            }
            else {
                show_legend(false, e.currentTarget.dataset.layerVariable);
            }
        });
    }
    init_remove_layer = function() {
        $(document).on('click', '.remove-action', function(e) {
            let $action_button = $(e.target);
            var $layer_label = $action_button.closest('.layers-context-menu').prev();
            var layer_id = ''

            var group_name = $layer_label.find('.layer-visibility-control').first().attr('name')

            if (!group_name) {
                var layer_name = $layer_label.find('.layer-group-visibility-control').first().data('layer-group-id')
            } else {
                var layer_name = $layer_label.find('.layer-visibility-control').first().data('layer-id')
                if (group_name == 'custom_layers') {
                    layer_id = $layer_label.find('.layer-visibility-control').first().data('layer-id')
                }
            }
            if (!layer_name) {
                return
            }
            var csrf_token = get_csrf_token();
            $('#do-action-button').on('click', function() {
                var new_name = $("#new-name-field").val()
                $.ajax({
                    type: 'POST',
                    url: window.location.href,
                    data: {'layer_name': layer_name,
                           'group_name': group_name,
                           'new_name': new_name,
                           'layer_id': layer_id,  // for custom layers
                           'method': 'remove_layer'},
                    beforeSend: xhr => {
                        xhr.setRequestHeader('X-CSRFToken', csrf_token);
                    },
                }).done(function (data) {

                })
            })
	    })
    };

    // Generate UUID
    generate_uuid = function () {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
        });
    }

    // get flow path data after condor completes
    function get_flow_path_json(remote_id){
        $.ajax({
            type: 'POST',
            url: '/apps/modflow/get-flow-path-json/',
            data: {'remote_id':remote_id}
        }).done(function (data) {
            if(data.success){
                // read features and separate, forward, backward, and starting features
                const format = new ol.format.GeoJSON();
                const features = format.readFeatures(data['data'], {
                                     defaultDataProjection: 'EPSG:4326',
                                     featureProjection:'EPSG:3857' })
                let forward_lines = []
                let backward_lines = []
                var starting_point_features = []
                for (let i = 0; i < features.length; i++) {
                  if (features[i]['values_']['direction'] == 'forward') {
                    forward_lines.push(features[i])
                  } else if (features[i]['values_']['direction'] == 'backward') {
                    backward_lines.push(features[i])
                  } else if (features[i]['values_']['attribute'] == 'starting_point') {
                    starting_point_features.push(features[i])
                  }
                }
                // Remove existing point
                clear_layer_name('modpath_point');
                const startptLayer = new ol.layer.Vector({
                    source: new ol.source.Vector({features: starting_point_features}),
                    style: new ol.style.Style({
                      fill: new ol.style.Fill({
                        color: 'rgba(255, 255, 255, 0.2)'
                      }),
                      stroke: new ol.style.Stroke({
                        color: '#ff3232',
                        width: 2
                      }),
                      image: new ol.style.Circle({
                        radius: 4,
                        fill: new ol.style.Fill({
                          color: '#ff3232'
                        })
                      })
                    })
                })

                const forward_style = new ol.style.Style({
                    stroke: new ol.style.Stroke({
                      color: '#0456db',
                      width: 3
                    }),
                })

                const backward_style = new ol.style.Style({
                    stroke: new ol.style.Stroke({
                      color: '#16e23c',
                      width: 3
                    }),
                })

                var start_pt_style = new ol.style.Style({
                  image: new ol.style.Circle({
                    radius: 7,
                    fill: new ol.style.Fill({color: 'black'}),
                    stroke: new ol.style.Stroke({
                      color: [255,0,0], width: 2
                    })
                  })
                })

                const forwardLayer = new ol.layer.Vector({
                  source: new ol.source.Vector({
                    features: forward_lines
                  }),
                  style: forward_style
                })

                const backwardLayer = new ol.layer.Vector({
                  source: new ol.source.Vector({
                    features: backward_lines
                  }),
                  style: backward_style
                })

                let flow_path_layer_group = new ol.layer.Group({
                    layers: [forwardLayer, backwardLayer, startptLayer]
                })
                flow_path_layer_group.set('name', 'flow_path_layer')

                // End Clean up
                // set up flow path group name here so that we can append to it later
                if (typeof particle_sol_group_name === 'undefined') {
                    particle_sol_group_name = 'Flow Path Result';
                }
                if (typeof particle_sol_group_id === 'undefined') {
                    particle_sol_group_id = generate_uuid();
                }
                if (typeof particle_count === 'undefined' ) {
                    particle_count = 1;
                }

                particle_uuid = [generate_uuid()];
                particle_sol_name = ['Flow Path of Particle ' + particle_count];
                particle_count = particle_count + 1
                let particle_legend = ['flowpath'];
                legend_layer_data['flowpath'].push(particle_uuid);

                ATCORE_MAP_VIEW.load_layers("results-tab-panel", particle_sol_group_name, particle_sol_group_id, [flow_path_layer_group], particle_sol_name, particle_uuid, particle_legend)
                ATCORE_MAP_VIEW.init_download_layer_action()
            } else {
                show_alert(data.message)
            }
            show_modpath_tool(true);
        })
        .fail(function() {
            show_alert('The model does not return valid result. Please contact customer support.');
            show_modpath_tool(true);
        })
    }

    var color_scale = ['#0000E1','#003ea3','#0080FF','#45A2B9','#A2D05C','#FFFF00','#FFD000','#FFA200','#FF7000','#FF3000']
    var color_scale_reverse = ['#FF3000','#FF7000', '#FFA200','#FFD000','#FFFF00','#A2D05C','#45A2B9','#0080FF','#003ea3', '#0000E1']
    var drawdown_color_scale = ['#3d04ff', '#7678ed', '#f7b801', '#f18701', '#f35b04']

    function get_drawdownColor(feature, feature_scale, property, opacity) {
        var num = feature['values_'][property]
        var mid;
        var lo = 0;
        var hi = feature_scale.length - 1;
        var hexColor;
        while (hi - lo > 1) {
            mid = Math.floor ((lo + hi) / 2);
            if (feature_scale[mid] < num) {
                lo = mid;
            } else {
                hi = mid;
            }
        }
        if (num - feature_scale[lo] <= feature_scale[hi] - num) {
            hexColor = drawdown_color_scale[lo];
        }
        else {
            hexColor = drawdown_color_scale[hi];
        }

        var color = ol.color.asArray(hexColor);
        color = color.slice();
        color[3] = opacity;
        return color;
    }

    function getColor(feature, feature_scale, property, reverse = false) {
        var num = feature['values_'][property]
        var mid;
        var lo = 0;
        var hi = feature_scale.length - 1;
        while (hi - lo > 1) {
            mid = Math.floor ((lo + hi) / 2);
            if (feature_scale[mid] < num) {
                lo = mid;
            } else {
                hi = mid;
            }
        }
        if (num - feature_scale[lo] <= feature_scale[hi] - num) {
            if (reverse){
                return color_scale_reverse[lo];
            }
            else {
                return color_scale[lo];
            }

        }
        if (reverse){
            return color_scale_reverse[hi];
        }
        else {
            return color_scale[hi];
        }

    }

    function pad(num, size) {
        var s = "000000000" + num;
        return s.substr(s.length-size);
    }

    function load_drawdown_result(data, legend) {
        let model_length_unit = $('#model_length_unit').data('value').toLowerCase();
        let model_time_unit = $('#model_time_unit').data('value').toLowerCase();

        // Clean up existing Data
        if (drawdown_uuid) {
            ATCORE_MAP_VIEW.remove_layer_from_map(drawdown_uuid);
        }
        if (drawdown_sol_group_id) {
            $('#' + drawdown_sol_group_id).remove();
            $('#' + drawdown_sol_group_id + "_associated_layers").remove();
        }
        // End Clean up
        drawdown_sol_group_name = 'Well Influence to Drawdown';
        drawdown_sol_group_id = generate_uuid();
        let drawdownlayerlist = [];
        let drawdown_sol_name_list = [];
        let drawdown_uuid_list = [];
        let drawdown_legend_list = [];

        for (var layer in data) {
            for (var sp in data[layer]) {
                drawdown_uuid = generate_uuid() + pad(layer, 3) + pad(sp, 3);
                drawdown_sol_name = 'Drawdown in ' + model_length_unit + ' Layer ' + layer + " Stress Period " + sp;
                const format = new ol.format.GeoJSON();
                let features = format.readFeatures(data[layer][sp], {
                                     defaultDataProjection: 'EPSG:4326',
                                     featureProjection:'EPSG:3857' })

                let drawdown_scale = legend

                let drawdownLayer = new ol.layer.Vector({
                  name: drawdown_uuid,
                  source: new ol.source.Vector({
                    features: features
                  }),
                  style: function(feature) {
                      return new ol.style.Style({
                          fill: new ol.style.Fill({
                            color: get_drawdownColor(feature, drawdown_scale, 'level', 0.3),
                          }),
                          stroke: new ol.style.Stroke({
                            color: get_drawdownColor(feature, drawdown_scale, 'level', 0.9),
                            width: 2,
                          }),
                      });
                    }
                })

                let drawdown_legend = create_drawdown_legends(drawdown_scale, drawdown_color_scale)
                $("#legend-drawdown .legend-list").html(drawdown_legend)

                drawdownLayer.set('name', 'drawdown_layer')

                drawdownlayerlist.push(drawdownLayer);
                drawdown_sol_name_list.push(drawdown_sol_name);
                drawdown_uuid_list.push(drawdown_uuid);
                drawdown_legend_list.push('drawdown');
            }
        }
//        drawdown_legend = "drawdown"



        ATCORE_MAP_VIEW.load_layers("results-tab-panel", drawdown_sol_group_name, drawdown_sol_group_id, drawdownlayerlist, drawdown_sol_name_list, drawdown_uuid_list, drawdown_legend_list, true)
        ATCORE_MAP_VIEW.init_download_layer_action()
        show_legend(true, 'drawdown');
        show_pump_impact_tool(true);
    }

    function load_stream_depletion_result(data, legend) {
        let model_length_unit = $('#model_length_unit').data('value').toLowerCase();
        let model_time_unit = $('#model_time_unit').data('value').toLowerCase();

        // Clean up existing Data
//        if (drawdown_uuid) {
//            ATCORE_MAP_VIEW.remove_layer_from_map(drawdown_uuid);
//        }
//        if (drawdown_sol_group_id) {
//            $('#' + drawdown_sol_group_id).remove();
//            $('#' + drawdown_sol_group_id + "_associated_layers").remove();
//        }
        // End Clean up
        stream_sol_group_name = "Well Influence to Stream";
        stream_sol_percentage_group_name = "Well Influence to Stream in Percentage";
        let stream_sol_group_id = generate_uuid();
        let streamflow_change_list = [];
        let streamflow_change_name_list = [];
        let streamflow_change_uuid_list = [];
        let streamflow_change_legend_list = [];

        let stream_sol_percentage_group_id = generate_uuid();
        let streamflow_percentage_list = [];
        let streamflow_percentage_name_list = [];
        let streamflow_percentage_uuid_list = [];
        let streamflow_percentage_legend_list = [];

        for (var layer in data) {
            for (var sp in data[layer]) {
                let streamflow_change_uuid = generate_uuid() + pad(layer, 3) + pad(sp, 3);
                let streamflow_change_name = 'Stream Depletion (gpm) Layer ' + layer + " Stress Period " + sp;
                let streamflow_percentage_uuid = generate_uuid() + pad(layer, 3) + pad(sp, 3);
                let streamflow_percentage_name = 'Percent (%) Stream Depletion Layer ' + layer + " Stress Period " + sp;

                let format = new ol.format.GeoJSON();
                let features = format.readFeatures(data[layer][sp], {
                                     defaultDataProjection: 'EPSG:4326',
                                     featureProjection:'EPSG:3857' })

                let streamflow_change_scale = legend['streamflow']
                let streamflow_percentage_scale = legend['streamflow_percentage']

                let streamflow_cfs_scale = []
                for (var i=0; i<streamflow_change_scale.length; i++) {
                    streamflow_cfs_scale[i] = streamflow_change_scale[i]
                }
                let streamflow_change_sum = streamflow_change_scale.reduce((a, b) => a +b, 0)
                let streamflow_change_reverse = streamflow_change_sum < 0 ? true : false;

                let streamflow_change_layer = new ol.layer.Vector({
                    name: streamflow_change_uuid,
                    source: new ol.source.Vector({
                      features: features
                    }),
                    style: function(feature) {
                        return new ol.style.Style({
                            fill: new ol.style.Fill({
                            color: getColor(feature, streamflow_change_scale, 'SF_Diff', streamflow_change_reverse)
                            })
                        });
                    },
                    opacity: 0.8,
                })

                let streamflow_percentage_sum = streamflow_percentage_scale.reduce((a, b) => a +b, 0)
                let streamflow_percentage_reverse = streamflow_percentage_sum < 0 ? true : false;
                let streamflow_percentage_layer = new ol.layer.Vector({
                    name: streamflow_percentage_uuid,
                    source: new ol.source.Vector({
                      features: features
                    }),
                    style: function(feature) {
                        return new ol.style.Style({
                            fill: new ol.style.Fill({
                            color: getColor(feature, streamflow_percentage_scale, 'SF_Diff', streamflow_percentage_reverse)
                            })
                        });
                    },
                    opacity: 0.8,
                })

                let streamflow_color_scale = streamflow_change_reverse ? color_scale_reverse : color_scale
                let streamflow_change_legend = create_pump_impact_legends(streamflow_cfs_scale, streamflow_color_scale)
                $("#legend-streamflow .legend-list").html(streamflow_change_legend)

                let streamflow_percentage_color_scale = streamflow_percentage_reverse ? color_scale_reverse : color_scale
                let streamflow_percentage_legend = create_pump_impact_legends(streamflow_percentage_scale, streamflow_percentage_color_scale)
                $("#legend-streamflow-percentage .legend-list").html(streamflow_percentage_legend)

                streamflow_change_list.push(streamflow_change_layer);
                streamflow_change_name_list.push(streamflow_change_name);
                streamflow_change_uuid_list.push(streamflow_change_uuid);
                streamflow_change_legend_list.push('streamflow');

                streamflow_percentage_list.push(streamflow_percentage_layer);
                streamflow_percentage_name_list.push(streamflow_percentage_name);
                streamflow_percentage_uuid_list.push(streamflow_percentage_uuid);
                streamflow_percentage_legend_list.push('streamflow-percentage');
            }
        }

        ATCORE_MAP_VIEW.load_layers("results-tab-panel", stream_sol_group_name, stream_sol_group_id, streamflow_change_list, streamflow_change_name_list, streamflow_change_uuid_list, streamflow_change_legend_list, true)
        ATCORE_MAP_VIEW.load_layers("results-tab-panel", stream_sol_percentage_group_name, stream_sol_percentage_group_id, streamflow_percentage_list, streamflow_percentage_name_list, streamflow_percentage_uuid_list, streamflow_percentage_legend_list, true)

        ATCORE_MAP_VIEW.init_download_layer_action()
        show_legend(true, 'streamflow');
        show_legend(true, 'streamflow-percentage');
        show_pump_impact_tool(true);
        group_layers_and_sp();
        bind_selector();
//        const format = new ol.format.GeoJSON();
//        const streamflow_features = format.readFeatures(data['streamflow_data'], {
//                             defaultDataProjection: 'EPSG:4326',
//                             featureProjection:'EPSG:3857' })
//
//        const streamflow_scale = legend["streamflow"]
//        let streamflow_cfs_scale = []
//        for (var i=0; i<streamflow_scale.length; i++) {
////            streamflow_cfs_scale[i] = streamflow_scale[i]/24/3600
//            streamflow_cfs_scale[i] = streamflow_scale[i]
//        }
//        let streamflow_sum = streamflow_scale.reduce((a, b) => a +b, 0)
//        let streamflow_reverse = streamflow_sum < 0 ? true : false;
//        const streamflowLayer = new ol.layer.Vector({
//            source: new ol.source.Vector({
//                features: streamflow_features
//            }),
//            style: function(feature) {
//                return new ol.style.Style({
//                    fill: new ol.style.Fill({
//                    color: getColor(feature, streamflow_scale, 'SF_Diff', streamflow_reverse)
//                    })
//                });
//            },
//            opacity: 0.8,
//        })
//
//        let streamflow_color_scale = streamflow_reverse ? color_scale_reverse : color_scale
//        let streamflow_legend = create_pump_impact_legends(streamflow_cfs_scale, streamflow_color_scale)
//        $("#legend-streamflow .legend-list").html(streamflow_legend)
//
//
//        const streamflow_percentage_scale = legend["streamflow_percentage"]
//        let streamflow_percentage_sum = streamflow_percentage_scale.reduce((a, b) => a +b, 0)
//        let streamflow_percentage_reverse = streamflow_percentage_sum < 0 ? true : false;
//        const streamflow_percentage_Layer = new ol.layer.Vector({
//            source: new ol.source.Vector({
//                features: streamflow_features
//            }),
//            style: function(feature) {
//                return new ol.style.Style({
//                    fill: new ol.style.Fill({
//                    color: getColor(feature, streamflow_percentage_scale, 'SF_Diff_Per', streamflow_percentage_reverse)
//                    })
//                });
//            },
//            opacity: 0.8,
//        })
//
//        let streamflow_percentage_color_scale = streamflow_percentage_reverse ? color_scale_reverse : color_scale
//        let streamflow_percentage_legend = create_pump_impact_legends(streamflow_percentage_scale, streamflow_percentage_color_scale)
//        $("#legend-streamflow-percentage .legend-list").html(streamflow_percentage_legend)
//
//
//        stream_sol_group_name = "Well Influence to Stream";
//        streamflow_sol_name = 'Change in Streamflow Out (' + model_length_unit + '^3/' + model_time_unit + ')';
////        streamflow_sol_name = 'Change in Streamflow Out (' + model_length_unit + '^3/Second' + ')';
//        streamflow_percentage_sol_name = 'Percent (%) Change in Streamflow Out';
//
//        // Clean up existing Data
//        if (streamflow_uuid) {
//            ATCORE_MAP_VIEW.remove_layer_from_map(streamflow_uuid);
//        }
//        if (streamflow_percentage_uuid) {
//            ATCORE_MAP_VIEW.remove_layer_from_map(streamflow_percentage_uuid);
//        }
//        if (stream_sol_group_id) {
//            $('#' + stream_sol_group_id).remove();
//            $('#' + stream_sol_group_id + "_associated_layers").remove();
//        }
//        // End Clean up
//
//        streamflow_uuid = 'StreamData_' + generate_uuid();
//        streamflow_percentage_uuid = 'StreamData_' + generate_uuid();
//        stream_sol_group_id = generate_uuid();
//        var layer_data = [streamflowLayer, streamflow_percentage_Layer];
//        var layer_names = [streamflow_sol_name, streamflow_percentage_sol_name]
//        var layer_ids = [streamflow_uuid, streamflow_percentage_uuid]
//        var layer_legends = ['streamflow', 'streamflow-percentage']
//
//        ATCORE_MAP_VIEW.load_layers("results-tab-panel", stream_sol_group_name, stream_sol_group_id, layer_data, layer_names, layer_ids, layer_legends, true)
//        ATCORE_MAP_VIEW.init_download_layer_action()
//        show_legend(true, 'streamflow');
//        show_legend(true, 'streamflow-percentage');
//        show_pump_impact_tool(true);
    }
    function get_pump_impact_json(remote_id, tool){
        $.ajax({
            type: 'POST',
            url: '/apps/modflow/get-pump-impact-json/',
            data: {'remote_id':remote_id, 'tool': tool}
        }).done(function (data) {
            if(data.success){
                let model_length_unit = $('#model_length_unit').data('value');
                let model_time_unit = $('#model_time_unit').data('value');
                if (tool == 'drawdown') {
                    load_drawdown_result(data['data'], data['legend']);
                } else if (tool == "stream_depletion") {
                    load_stream_depletion_result(data['data'], data['legend'])
                }
                else {
                    load_drawdown_result(data['data']['drawdown'], data['legend']['drawdown']);
                    load_stream_depletion_result(data['data']['streamflow_data'], data['legend'])
                }
            } else {
                show_alert(data.message)
                show_pump_impact_tool(true)
            }
        })
    }

    create_pump_impact_legends = function(scale, color_scale) {
        var legend = '';
        var legend_value = 0
        for (let i = 1; i < scale.length; i++) {
            if (Math.abs(scale[i]) < 0.1) {
                legend_value = scale[i].toFixed(3);
            }
            else if (Math.abs(scale[i]) < 1) {
                legend_value = scale[i].toFixed(2);
            }
            else if (Math.abs(scale[i]) < 10) {
                legend_value = scale[i].toFixed(1);
            }
            else {
                legend_value = scale[i].toFixed(0);
            }
            legend += "<div class='legend-item'><li class='legend-list-item'><p>";
            legend += legend_value + "</p><div class='color-box' style='background-color:";
            legend += color_scale[i] + "'></div></li></div>";
        }
        return legend
    }

    create_drawdown_legends = function(scale, color_scale) {
        var legend = '';
        for (let i = 0; i < scale.length; i++) {
            legend += "<div class='legend-item'><li class='legend-list-item'><p> >= ";
            legend += scale[i] + "</p><div class='color-box' style='background-color:";
            legend += color_scale[i] + "'></div></li></div>";
        }
        return legend
    }

    function update_status(workflow_id, remote_id, workflow){
        const refresh_interval = 5000;
        $.ajax({
            method: 'POST',
            url: '/apps/modflow/check-job-status/',
            data: {'workflow': workflow, 'workflow_id': workflow_id}
        }).done(function(json){
            if(json.success){
                status = json.status;
                if (status == 'Running' || status == 'Submitted' || status == 'Various'){
                    setTimeout(function(){
                        update_status(workflow_id, remote_id, workflow);
                    }, refresh_interval);
                } else if (status == 'Complete' || status == 'Aborted') {
                    if (workflow == 'flow_path') {
                        $("#modpath-status-bar").html('');
                        $("#modpath-status-bar").addClass('hidden')
                        // Show legend if complete
                        if (status == 'Complete') {
                            get_flow_path_json(remote_id);
                            show_legend(true, 'flowpath');
                        }
                    } else {
                        if (status == 'Complete') {
                            get_pump_impact_json(remote_id, workflow);
                            if (workflow == 'drawdown') {
                                show_legend(true, 'drawdown')
                            }
                            else if (workflow == 'stream_depletion') {
                                show_legend('true', 'streamflow');
                            }
                        }
                        $("#pump-impact-status-bar").html('')
                    }
                }
            } else {
                show_alert("An unexpected error has occurred. Please try again.")
                if (workflow == 'flow_path') {
                    show_modpath_tool(true);
                } else {
                    show_pump_impact_tool(true);
                }
            }
        });
    }

    init_flow_path_creation = function(count) {
        $("#modpath-init").toggleClass("selected");
        if ($("#modpath-init").hasClass('selected')) {
            clear_layer_name('modpath_point');
            let vectorlayer = add_map_interaction('Point', 'flow_path')
            vectorlayer.set('name', 'modpath_point')
            m_map.addLayer(vectorlayer)
            $("#modpath-init").val(true)
        } else {
            remove_map_interaction('Point')
            $("#modpath-init").val(false)
        }
    };

    flow_path_listener = function () {
        m_map.on('singleclick', function (evt) {
            if ($("#modpath-init").val()) {
                if ($("#modpath-init").hasClass('selected')) {
                    let lonlat = ol.proj.transform(evt.coordinate, 'EPSG:3857', 'EPSG:4326');
                    let lon = lonlat[0].toFixed(5);
                    let lat = lonlat[1].toFixed(5);
                    var point = [lat, lon];
                    // Get id from tethys_data attribute
                    m_map.getLayers().forEach(function(item, index, array) {
                        if ('tethys_data' in item && 'layer_id' in item.tethys_data) {
                           if (typeof(item.tethys_data.layer_id) == "string") {
                               if(item.tethys_data.layer_id.search('model_boundary') > 0) {
                                   let boundary_layer = m_layers[item.tethys_data.layer_id];
                                   $.ajax({
                                       method: 'get',
                                       url: '/apps/modflow/check-point-status/',
                                       data: {'layer_id': JSON.stringify(item.tethys_data.layer_id),
                                              'point_location': JSON.stringify(point),
                                              'inprj': '4326',
                                             },
                                       async: false
                                   }).done(function(json){
                                       if(json.success){
                                           if (!json.status) {
                                               show_alert("Starting Location is outside of model boundary");
                                               clear_layer_name('modpath_point');
                                               let vectorlayer = add_map_interaction('Point', 'flow_path')
                                               vectorlayer.set('name', 'modpath_point')
                                               m_map.addLayer(vectorlayer)
                                           }
                                           else {
                                               let resource_id = window.location.pathname.split('/').reverse()[2];
                                               let depth = $("#flow_path_depth").val()
                                               if (depth == "") {
                                                    depth = 0
                                               }
                                               remove_map_interaction();
                                               show_modpath_tool(false);
                                               $.ajax({type: 'POST',
                                                    url: '/apps/modflow/modpath/',
                                                    data: {'resource_id':resource_id,
                                                           'lon':lon,
                                                           'lat':lat,
                                                           'depth': depth}
                                                    })
                                               .done(function (data) {
                                                    if(data.success){
                                                        update_status(data.workflow_id, data.remote_id, 'flow_path')
                                                    } else {
                                                        show_alert(data.message)
                                                    }
                                               })
                                           }
                                       }
                                   });
                               }
                           }
                        }
                     });
                }
            $("#modpath-init").val(false)
            }
        })
    }

    add_map_interaction = function(draw_type, tool) {
        remove_map_interaction()
        let source = new ol.source.Vector();
        let vector = new ol.layer.Vector({
            source: source,
            style: new ol.style.Style({
              fill: new ol.style.Fill({
                color: 'rgba(255, 255, 255, 0.2)'
              }),
              stroke: new ol.style.Stroke({
                color: '#ff3232',
                width: 2
              }),
              image: new ol.style.Circle({
                radius: 4,
                fill: new ol.style.Fill({
                  color: '#ff3232'
                })
              })
            })
        })

        draw = new ol.interaction.Draw({
          source: source,
          type: draw_type
        });
        m_map.addInteraction(draw);

        snap = new ol.interaction.Snap({source: source});
        m_map.addInteraction(snap);

        return vector
    };

    remove_map_interaction = function() {
        m_map.removeInteraction(draw)
    };

    remove_temporary_layers = function(tool) {
        var layersToRemove = [];
        m_map.getLayers().forEach(function (layer) {
            if (tool == 'modpath' && layer.get('name')  === 'flow_path_layer') {
                show_legend(false, 'flowpath');
                layersToRemove.push(layer)
//            } else if (tool == 'pump_impact' && layer.get('name')  === 'pump_impact_layer') {
            }
        });

        var len = layersToRemove.length;
        for(var i = 0; i < len; i++) {
            m_map.removeLayer(layersToRemove[i]);
        }

        // Remove solution layer
        let layers_to_remove = [streamflow_uuid, drawdown_uuid, streamflow_percentage_uuid];
        var i;
        for (i = 0; i < layers_to_remove.length; i++) {
            if (layers_to_remove[i]) {
                ATCORE_MAP_VIEW.remove_layer_from_map(layers_to_remove[i]);
            }
        }
        // Remove Tree Items
        let id_to_remove_list = [stream_sol_group_id, drawdown_sol_group_id, particle_sol_group_id];

        var i;
        for (i = 0; i < id_to_remove_list.length; i++) {
            if (id_to_remove_list[i]) {
                $('#' + id_to_remove_list[i]).remove();
                $('#' + id_to_remove_list[i] + "_associated_layers").remove();
            }
        }

        $("#legend-streamflow").addClass("hidden");
        $("#legend-streamflow-percentage").addClass("hidden");
        $("#legend-drawdown").addClass("hidden");
    }

    init_slide_sheet = function() {
        bind_flow_path_buttons()
        bind_pump_impact_buttons()
        slide_sheet_close_event()
    };

    bind_flow_path_buttons = function() {
        // Reset click events on flow_path buttons
        $('.btn-flow_path').off('click');

        // Call load_flow_path when buttons are clicked
        $('.btn-flow_path').on('click', function(e) {
            // Load the flow_path
            load_flow_path();
            $(".pump_marker").removeClass('selected')
            remove_map_interaction('Point')
        });
    };

    load_flow_path = function() {
        // Show the flow_path slide sheet
        SLIDE_SHEET.close('pump-impact-slide-sheet');
        remove_map_interaction();
        show_flow_path();
    };

    show_flow_path = function() {
        SLIDE_SHEET.open('flow-path-slide-sheet');
        remove_map_interaction();
    };

    slide_sheet_close_event = function() {
        $('.close').on('click', function() {
            remove_map_interaction();
            $('.selected').removeClass('selected');
        })
    }

    bind_pump_impact_buttons = function() {
        // Reset click events on flow_path buttons
        $('.btn-pump_impact').off('click');

        // Call load_flow_path when buttons are clicked
        $('.btn-pump_impact').on('click', function(e) {
            // Load the flow_path
            load_pump_impact();
            $("#modpath-init").removeClass('selected')
            remove_map_interaction('Point')
            update_unit()
        });
    };

    load_pump_impact = function() {
        // Show the flow_path slide sheet
        SLIDE_SHEET.close('flow-path-slide-sheet');
        remove_map_interaction();
        show_legend(false, 'flowpath')
        show_pump_impact();
    };

    show_pump_impact = function() {
        SLIDE_SHEET.open('pump-impact-slide-sheet');
        remove_map_interaction();
    };

    remove_feature = function(name) {
        m_map.getLayers().forEach(function (layer) {
            if (typeof layer !== 'undefined') {
                if (layer.get('name')  === name) {
                    m_map.removeLayer(layer);
                }
            }
        });
    }

    location_pump_impact = function() {
        $(document).on('click', '.pump_marker', function() {
            let pump_button = $(this)
            let old_layer_name = pump_button.data('layer')
            if (pump_button.data('layer')) {
                remove_feature(old_layer_name);
            }

            // Clear all selected class
            $(".selected").removeClass('selected');

            let draw_type;
            let location;
            if ($('#transient_model').val() == 'True') {
                draw_type = pump_button.closest('tr').find("td:eq(4)").find(':selected').val()
                location = pump_button.closest('tr').find("td:eq(5) input");
            }
            else {
                draw_type = pump_button.closest('tr').find("td:eq(2)").find(':selected').val()
                location = pump_button.closest('tr').find("td:eq(3) input")
            }

            let layer_number = pump_button.closest('tr').find("th:eq(0)").text()
            let layer_name = 'vectorlayer' + layer_number
            pump_button.addClass("selected");

            let vectorlayer = add_map_interaction(draw_type, 'pump_impact')

            if (pump_button.hasClass('selected')) {
                vectorlayer.getSource().on('addfeature', function(event){
                    vectorlayer.set('name', layer_name)
                    m_map.addLayer(vectorlayer)
                    pump_button.data('layer', layer_name)
                    let features = vectorlayer.getSource().getFeatures();
                    let coord_dict = ''
                    features.forEach(function(feature) {
                        let coords = feature.getGeometry().getCoordinates();
                        if (draw_type == 'Point') {
                            let lonlat = ol.proj.transform(coords, 'EPSG:3857', 'EPSG:4326');
                            let lon = lonlat[0].toFixed(5);
                            let lat = lonlat[1].toFixed(5);
                            coord_dict = coord_dict + lat + ',' + lon
                            location.val(coord_dict)
                        } else {
                            for (let i = 1; i < coords[0].length; i++) {
                                let lonlat = ol.proj.transform(coords[0][i], 'EPSG:3857', 'EPSG:4326');
                                let lon = lonlat[0];
                                let lat = lonlat[1];
                                coord_dict = coord_dict + lat + ',' + lon
                                if (i != coords[0].length -1) {
                                    coord_dict = coord_dict + ';'
                                }
                            }
                            location.val(coord_dict)
                        }
                    });
                    remove_map_interaction(draw_type)
                    pump_button.toggleClass("selected");
                });
            }
        });
    }

    delete_row_pump_impact = function() {
        $(document).on('click', '.delete_row', function() {
            let delete_button = $(this)
            let pump_button;
            if ($('#transient_model').val() == 'True') {
                pump_button = delete_button.closest('tr').find("td:eq(8) button")
            }
            else {
                pump_button = delete_button.closest('tr').find("td:eq(6) button")
            }
            let old_layer_name = pump_button.data('layer')
            if (pump_button.data('layer')) {
                m_map.getLayers().forEach(function (layer) {
                    if (layer) {
                        if (layer.get('name') == old_layer_name) {
                            m_map.removeLayer(layer);
                        }
                    }
                });
            }
            $(this).parents('tr').remove()
            let newRowCount = 0
            $('#pump_impact_table > tbody  > tr').each(function() {
                newRowCount = newRowCount + 1
                let old_number = $(this).find("th:eq(0)").html()
                $(this).find("th:eq(0)").html(newRowCount)
                let pump_button = $(this).find("td:eq(4) button")
                let old_layer_name = pump_button.data('layer')
                let new_layer_name = 'vectorlayer' + newRowCount
                if (pump_button.data('layer')) {
                    m_map.getLayers().forEach(function (layer) {
                        if (layer) {
                            if (layer.get('name') == old_layer_name) {
                                layer.set('name', new_layer_name)
                                pump_button.data('layer', new_layer_name)
                            }
                        }
                    });
                }
            });
        });
    }

    create_point_from_latlon = function(input_str) {
        // -112.05230712890625,46.2126253904882;-111.97952270507812,46.254422478837654;-112.08114624023435,46.2430264298832
        let input_points = input_str.val().split(";")
        let layer_number = input_str.closest('tr').find("th:eq(0)").text()
        let pump_button = input_str.closest('tr').find("td:eq(4) button")
        let layer_name = 'vectorlayer' + layer_number
        if (pump_button.data('layer')) {
            m_map.getLayers().forEach(function (layer) {
                if (layer) {
                    if (layer.get('name') == layer_name) {
                        m_map.removeLayer(layer);
                    }
                }
            });
        }
        if (input_points.length == 1) {
            let input_point = input_points[0].split(",")
            let points = []
            for (var i=0,l=input_point.length;i<l;i++) {
                points.push(parseFloat(input_point[i]));
            }
            var point = new ol.geom.Point(points);
            point.transform('EPSG:4326', 'EPSG:3857');
            var feature = new ol.Feature({
                geometry: point,
                name: 'pump_created_point'
            });
        } else {
            let polyline_points = []
            for (var i=0,l=input_points.length;i<l;i++) {
                let point_str = input_points[i].split(",")
                let point_float = ol.proj.transform([parseFloat(point_str[1]), parseFloat(point_str[0])], 'EPSG:4326', 'EPSG:3857')
                polyline_points.push(point_float);
            }
            var feature = new ol.Feature({
                geometry: new ol.geom.Polygon([polyline_points])
            })
        }
        var vectorSource = new ol.source.Vector({
           features: [feature]
        });
        var vectorLayer = new ol.layer.Vector({
            source: vectorSource,
            style: new ol.style.Style({
              fill: new ol.style.Fill({
                color: 'rgba(255, 255, 255, 0.2)'
              }),
              stroke: new ol.style.Stroke({
                color: '#ff3232',
                width: 2
              }),
              image: new ol.style.Circle({
                radius: 4,
                fill: new ol.style.Fill({
                  color: '#ff3232'
                })
              })
            })
        });
        vectorLayer.set('name', layer_name)
        m_map.addLayer(vectorLayer)
        pump_button.data('layer', layer_name)
    }

    add_pump_impact_row = function() {
        //Get Unit from model
        let model_length_unit = $('#model_length_unit').data('value').toLowerCase();
        let model_time_unit = $('#model_time_unit').data('value').toLowerCase();
        let gpm_conversion = 0;
        if (model_length_unit == 'feet' && model_time_unit == 'day') {
            gpm_conversion = 190.50;
        }

        let rowCount = $('#pump_impact_table tbody tr').length;
        let row_id = rowCount +1
        let row_name = 'vectorlayer' + String(row_id);
        let well_id = 'well_id' + String(row_id);
        let newRowContent = '<tr><th scope="row">' + (rowCount + 1) + '</th><td><input class="' + well_input_name + '" id="' + well_input_name + String(row_id) + '" type="text"><input class="PumpingScheduleButton'
        if (!$('#transient_model').val()) {
            newRowContent += ' hidden';
        }
        newRowContent += '" type="button" title="Input Pumping Schedule" value="..." data-layer="' + row_name + '" id="' + well_id + '"></td>'
        newRowContent += '<td class="unit_type" data-name="unit_layer' + String(row_id) + '"><select id="unit_layer_well_id' + String(row_id) + '"><option value="-1">' + model_length_unit + '&sup3;/' + model_time_unit + '</option>'
        if (gpm_conversion >0) {
            newRowContent = newRowContent + '<option value="-' + gpm_conversion + '" selected>gpm</option>'
        }
        newRowContent = newRowContent + '</select></td>'
        if ($('#transient_model').val()) {
            newRowContent = newRowContent + '<td><input id="StartTime' + row_id + '" class="StartTime" value="" title="If empty, Pumping Rate is Constant" placeholder=""></td>'
            newRowContent = newRowContent + '<td><input id="Duration' + row_id + '" class="Duration" value=""></td>'
        }
        newRowContent = newRowContent + '<td class="vector_type" data-name="' + row_name + '"><select><option value="Point">Well</option>' + '<option value="Polygon">Well Field</option></select></td>'
        newRowContent = newRowContent + '<td class="pump_location"><input class="location_input"></td>'
        newRowContent = newRowContent + '<td><input id="PumpDepthInput' + row_id + '" class="PumpDepthInput" value=0></td>'
        newRowContent = newRowContent + '<td style="width: 1%;"><button type="button" ' +
            'class="btn btn-default slide-sheet-btn pump_marker center-btn" data-layer="' + row_name + '" ' +
            'data-toggle="tooltip" data-placement="top">' +
            'Draw on Map</button></td>'
        newRowContent = newRowContent + '<td style="width: 1%;"><button type="button" ' +
            'class="btn btn-default slide-sheet-btn delete_row center-btn" data-toggle="tooltip" data-placement="top" data-layer="' + row_name + '" ' +
            'value="Remove">Remove</button></td>'
        newRowContent = newRowContent + '</tr>'
        $("#pump_impact_table tbody").append(newRowContent);
//        $("." + well_input_name).inputFilter(function(value) {
//            return /^\d*$/.test(value);
//        });
        $(".PumpDepthInput").inputFilter(function(value) {
            return /^\d*$/.test(value);
        });
        $(".vector_type").on('change', function() {
            remove_map_interaction('Point');
            remove_map_interaction('Polygon');
            remove_feature($(this).data('name'));
            // Clear lon, lat value
            if ($(this).next('td').children('input').length > 0) {
                $(this).next('td').children('input')[0].value = "";
            }


        });
        $('.location_input').on('keypress',function(e){
            if(e.which == 13) {
                create_point_from_latlon($(this))
            }
        });

        $('#' + well_input_name + row_id).on('change', function(event) {
            // if input value is string, this means it's using pumping schedule
            if (isNaN($(this).val())) {
                SPATIAL_DATA_MWV.disable_start_duration_field(row_id);
//                $('#StartTime' + row_id).prop('disabled', true);
//                $('#StartTime' + row_id).prop('placeholder', 'Use Pumping Schedule');
//                $('#Duration' + row_id).prop('disabled', true);
//                $('#Duration' + row_id).prop('placeholder', 'Use Pumping Schedule');
            }
            else {
                SPATIAL_DATA_MWV.enable_start_duration_field(row_id);
//                $('#StartTime' + row_id).prop('disabled', false);
//                $('#StartTime' + row_id).prop('placeholder', '');
//                $('#Duration' + row_id).prop('disabled', false);
//                $('#Duration' + row_id).prop('placeholder', '');
            }
        })

        $('#' + well_id).on('click', function(event) {
            let x = event.pageX;
            let y = event.pageY;
            m_$data_popup_container.css('display', 'block');
//            m_$data_popup_container.css('top', '10%');
//            m_$data_popup_container.css('left', '25%');
            let feature_id = String(parseInt(rowCount) + parseInt(1))
            let data = $('#' + well_input_name + feature_id).val();
            data = data.replace(/;/g, "_")
            let pump_unit = $('#unit_layer_' + well_id).find(":selected").text()
            m_$data_popup_content.load('/apps/modflow/pump-schedule-data', 'data=' + data + '&well_id=' + feature_id + '&unit=' + pump_unit + '&time_unit=' + model_time_unit, function(content, status){
                if (status == "success") {
                    SPATIAL_DATASET_MWV.after_form_load();
//                    m_$data_popup_content.html(content);
                }
            });
        })
    }

    var processData_ps = function () {
        console.log('test')
    }

    run_pump_impact_tool = function() {
        let data = {}
        let ajax_status = true
        var features = {
            "name":"NewFeatureType",
            "type":"FeatureCollection",
            "features":[]
        };
        // Only run tool if we can find at least one none 0 flowrate.
        var run_pump_impact = false;
        if (!$('#stream_depletion_status').prop('checked') && !$('#drawdown_status').prop('checked')) {
            show_alert('Please select at least one workflow');
            return false;
        }
        $('#pump_impact_table > tbody  > tr').each(function() {
            let number = $(this).find("th:eq(0)").html()
            let flowrate = $(this).find("td:eq(0) input").val()
            if(flowrate) {
                run_pump_impact = true;
            }
            let pump_factor = $(this).find("td:eq(1) select").val();
            let well_type;
            let location;
            let depth;
            let start_time = "";
            let duration = "";
            if ($('#transient_model').val() == 'True') {
                start_time = $(this).find("td:eq(2) input").val()
                duration = $(this).find("td:eq(3) input").val()
                if (start_time !== '') {
                    let endtime = parseFloat(start_time) + parseFloat(duration)
                    flowrate = start_time + "," + flowrate + ";" + endtime + "," + flowrate;
                }
                well_type = $(this).find("td:eq(4) select").val()
                location = $(this).find("td:eq(5) input").val().split(";");
                depth = $(this).find("td:eq(6) input").val();
            }
            else {
                well_type = $(this).find("td:eq(2) select").val()
                location = $(this).find("td:eq(3) input").val().split(";");
                depth = $(this).find("td:eq(4) input").val();
            }
            if (location.length == 1) {
                var point = location[0].split(",");
                // Get id from tethys_data attribute
                m_map.getLayers().forEach(function(item, index, array) {
                    if ('tethys_data' in item && 'layer_id' in item.tethys_data) {
                       if (typeof(item.tethys_data.layer_id) == "string") {
                           if(item.tethys_data.layer_id.search('model_boundary') > 0) {
                               let boundary_layer = m_layers[item.tethys_data.layer_id];
                               $.ajax({
                                   method: 'get',
                                   url: '/apps/modflow/check-point-status/',
                                   data: {'layer_id': JSON.stringify(item.tethys_data.layer_id),
                                          'point_location': JSON.stringify(point),
                                          'inprj': '4326',
                                         },
                                   async: false
                               }).done(function(json){
                                   if(json.success){
                                       if (!json.status) {
                                           show_alert("Well " + number + " is outside model boundary");
                                           ajax_status = false;
                                       }
                                   }
                               });
                           }
                           if(item.tethys_data.layer_id.search('model_grid') > 0) {
                               let boundary_layer = m_layers[item.tethys_data.layer_id];
                               $.ajax({
                                   method: 'get',
                                   url: '/apps/modflow/check-well-depth/',
                                   data: {'layer_id': JSON.stringify(item.tethys_data.layer_id),
                                          'point_location': JSON.stringify(point),
                                          'inprj': '4326',
                                          'depth': depth,
                                         },
                                   async: false
                               }).done(function(json){
                                   if(json.success){
                                       if (!json.status) {
                                           if (json.thickness !== "") {
                                               show_alert("Well " + number + " depth (" + depth + ") is greater than model thickness of " + json.thickness.toFixed(1) +" at this location" );
                                               ajax_status = false;
                                           }
                                       }
                                   }
                               });
                           }
                       }
                    }
                 });
                var geometry_data = {"type": "Point",
                                    "coordinates": [parseFloat(point[1]), parseFloat(point[0]), parseFloat(depth)]}
            } else {
                var geometry_data = {"type": "Polygon",
                                    "coordinates": [[]]}
                for (var i = 0; i < location.length; i++) {
                    var point = location[i].split(",")
                    // Get id from tethys_data attribute
                    m_map.getLayers().forEach(function(item, index, array) {
                        if ('tethys_data' in item && 'layer_id' in item.tethys_data) {
                           if (typeof(item.tethys_data.layer_id) == "string") {
                               if(item.tethys_data.layer_id.search('model_boundary') > 0) {
                                   let boundary_layer = m_layers[item.tethys_data.layer_id];
                                   $.ajax({
                                       method: 'get',
                                       url: '/apps/modflow/check-point-status/',
                                       data: {'layer_id': JSON.stringify(item.tethys_data.layer_id),
                                              'point_location': JSON.stringify(point),
                                              'inprj': '4326',
                                             },
                                       async: false
                                   }).done(function(json){
                                       if(json.success){
                                           if (!json.status) {
                                               show_alert("Well Field " + number + " is outside model boundary");
                                               ajax_status = false;
                                           }
                                       }
                                   });
                               }
                           }
                        }
                     });
                    geometry_data['coordinates'][0].push([parseFloat(point[1]), parseFloat(point[0])])
                }
                let close_point = location[0].split(",")
                geometry_data['coordinates'][0].push([parseFloat(close_point[1]), parseFloat(close_point[0])])
            }

            var feature = {
                "type":"Feature",
                "geometry": geometry_data,
                "properties": {'Flowrate' : flowrate, 'ID': number, 'Pumpfactor': pump_factor}
            }

            if (!location[0]) {
                show_alert("Please provide a location for well #" + $(this).find("th:eq(0)").html() + '.')
                ajax_status = false
                return
            }
            if (!depth) {
                show_alert("Please provide a depth for well #" + $(this).find("th:eq(0)").html() + '.')
                ajax_status = false
                return
            }
            features['features'].push(feature)
        })

        if (!ajax_status){
            return
        }

        if (!features['features'].length) {
            show_alert("Please provide well inputs.")
            return
        }

        if (!run_pump_impact) {
            show_alert("At least one of well needs to have none zero value.")
            return;
        }
        let resource_id = window.location.pathname.split('/').reverse()[2];
        show_pump_impact_tool(false)

        let tool = '';
        let input = '';
        let layer_output = '';
        let stress_period_output = '';
        if ($('#output_layer').val()) {
            layer_output = $('#output_layer').val();
        }
        if ($('#output_stress_period').val()) {
            stress_period_output = $('#output_stress_period').val();
        }
        if ($('#stream_depletion_status').prop('checked')) {
            tool='stream_depletion';
            input = $('#stream_depletion_tolerance').val()
        }
        if ($('#drawdown_status').prop('checked')) {
            if (tool == 'stream_depletion') {
                tool = 'drawdown;stream_depletion';
                input = $('#drawdown_interval').val() + ";" + $('#stream_depletion_tolerance').val()
            }
            else {
                tool = 'drawdown';
                input = $('#drawdown_interval').val()
            }
        }

        $.ajax({
            type: 'POST',
            url: '/apps/modflow/pump-impact/',
            data: {'data':JSON.stringify(features),
                   'resource_id': resource_id,
                   'package': '',
                   'tool': tool,
                   'input': input,
                   'layer': layer_output,
                   'stress_period_output': stress_period_output,
            }
        }).done(function (data) {
            if(data.success){
                update_status(data.workflow_id, data.remote_id, tool)
            } else {
                show_alert(data.message);
                show_pump_impact_tool(true);
            }
        })
    }
    clear_layer_name = function(name) {
        m_map.getLayers().forEach(function (layer) {
                    if (layer.get('name')  === name) {
                        m_map.removeLayer(layer);
                    }
                })
    }

    cancel_job = function(name) {
        let resource_id = window.location.pathname.split('/').reverse()[2];
        if (name == 'modpath') {
            $.ajax({
                type: 'POST',
                url: '/apps/modflow/modpath/',
                data: {'resource_id':resource_id,
                       'cancel': true}
            }).done(function (data) {
                show_modpath_tool(true);
                clear_layer_name('modpath_point');
                show_legend(false, 'flowpath');
            }).fail(function() {
                show_modpath_tool(true);
            })
        }
        else if (name == 'well_influence') {
            $.ajax({
            type: 'POST',
            url: '/apps/modflow/pump-impact/',
            data: {'resource_id':resource_id,
                   'cancel': true}
            }).done(function (data) {
                show_pump_impact_tool(true);
            }).fail(function() {
                show_pump_impact_tool(true);
            })
        }
    }

    show_modpath_tool = function(status) {
        if (status) {
            $("#modpath-init").prop("disabled", false);
            $("#modpath-status-bar").addClass("hidden");
            $("#modpath-status-bar").html("");
            $(".modpath-status").addClass("hidden");
            $("#btn-cancel-modpath").addClass("hidden");
            $(".btn-flow_path").removeClass("not-active");
            $(".btn-pump_impact").removeClass("not-active");
        }
        else {
            $("#modpath-init").prop("disabled", true);
            $("#modpath-status-bar").removeClass("hidden");
            $(".modpath-status").removeClass("hidden");
            $("#modpath-status-bar").html("<div class='modpath-status-child'><span class='text-dark text-model-running' style='padding: 10px'><strong>Please be patient, this may take a while. </strong></span></p><p><img src='/static/modflow/images/loading3.gif'/></p><p><button onclick=\"MODFLOW_MODEL_MAP_VIEW.cancel_job('modpath')\" class=\"btn btn-default hidden\" id=\"btn-cancel-modpath\">Cancel </button></></div>");
            $("#btn-cancel-modpath").removeClass("hidden");
            $(".btn-flow_path").addClass("not-active");
            $(".btn-pump_impact").addClass("not-active");
        }

    }

    show_pump_impact_tool = function(status) {
        if (status) {
            $("#run-drawdown-btn").prop("disabled", false);
            $("#run-stream-depletion-btn").prop("disabled", false);
            $("#pump-impact-status-bar").addClass("hidden");
            $("#pump-impact-status-bar").html("");
            $(".pump-impact-status").addClass("hidden");
            $("#btn-cancel-well-influence").addClass("hidden");
            $(".btn-flow_path").removeClass("not-active");
            $(".btn-pump_impact").removeClass("not-active");
        }
        else {
            $("#run-drawdown-btn").prop("disabled", true);
            $("#run-stream-depletion-btn").prop("disabled", true);
            $("#pump-impact-status-bar").removeClass("hidden");
            $(".pump-impact-status").removeClass("hidden");
            $("#pump-impact-status-bar").html("<div class='pump-impact-status-child'><span class='text-dark text-model-running' style='padding: 10px'><strong>Please be patient, this may take a while. </strong></span></p><p><img src='/static/modflow/images/loading3.gif'/></p><p><button onclick=\"MODFLOW_MODEL_MAP_VIEW.cancel_job('well_influence')\" class=\"btn btn-default hidden\" id=\"btn-cancel-well-influence\">Cancel </button></></div>");
            $("#btn-cancel-well-influence").removeClass("hidden");
            $(".btn-flow_path").addClass("not-active");
            $(".btn-pump_impact").addClass("not-active");
        }
    }

    show_legend = function(status, name) {
        if (status) {
            $('#legend-' + name).removeClass('hidden');
        }
        else {
            if (name == 'flowpath') {
                // Loop through legend_layer_data to find if the checked status of the remaining layers
                let turn_off_legend = true
                let layer_checked = false
                for (var i=0; i < legend_layer_data[name].length; i++) {
                    if ($('.layer-visibility-control[data-layer-id="' + legend_layer_data[name][i] + '"]').length > 0) {
                        layer_checked = $('.layer-visibility-control[data-layer-id="' + legend_layer_data[name][i] + '"]')[0].checked
                    }
                    if (layer_checked) {
                        turn_off_legend = false;
                        break;
                    }
                }
                if (turn_off_legend) {
                    $('#legend-' + name).addClass('hidden');
                }
                else {
                    $('#legend-' + name).removeClass('hidden');
                }
            }
            else {
                $('#legend-' + name).addClass('hidden');
            }
        }

    }

    update_unit = function() {
        //Get Unit from model
        let model_length_unit = $('#model_length_unit').data('value').toLowerCase();
        let model_time_unit = $('#model_time_unit').data('value').toLowerCase();

        // Update unit
        let change_list = $('.unit-update')
        let i;
        for (i = 0; i < change_list.length; i++) {
            let html_content = $(change_list.get(i)).html()
            if (html_content.includes('#length_unit#')) {
                html_content = html_content.replace('#length_unit#', model_length_unit)
            }
            if (html_content.includes('#time_unit#')) {
                html_content = html_content.replace('#time_unit#', model_time_unit)
            }
            $(change_list.get(i)).html(html_content)
        }
    }

    check_point_inside = function (point) {
         m_map.getLayers().forEach(function(item, index, array) {
            if ('tethys_data' in item && 'layer_id' in item.tethys_data) {
               if (typeof(item.tethys_data.layer_id) == "string") {
                   if(item.tethys_data.layer_id.search('model_boundary') > 0) {
                       let boundary_layer = m_layers[item.tethys_data.layer_id];
                       $.ajax({
                           method: 'get',
                           url: '/apps/modflow/check-point-status/',
                           data: {'layer_id': JSON.stringify(item.tethys_data.layer_id),
                                  'point_location': JSON.stringify(point),
                                  'inprj': '4326',
                                 },
                           async: false
                       }).done(function(json){
                           if(json.success){
                               if (!json.status) {
                                   console.log("Point is outside");
                                   return false;
                               }
                               else {
                                   return true;
                               }
                           }
                       });
                   }
               }
            }
         });
    }

    check_well_depth = function (point) {
         m_map.getLayers().forEach(function(item, index, array) {
            if ('tethys_data' in item && 'layer_id' in item.tethys_data) {
               if (typeof(item.tethys_data.layer_id) == "string") {
                   if(item.tethys_data.layer_id.search('model_boundary') > 0) {
                       let boundary_layer = m_layers[item.tethys_data.layer_id];
                       $.ajax({
                           method: 'get',
                           url: '/apps/modflow/check_well_depth/',
                           data: {'layer_id': JSON.stringify(item.tethys_data.layer_id),
                                  'point_location': JSON.stringify(point),
                                  'inprj': '4326',
                                 },
                           async: false
                       }).done(function(json){
                           if(json.success){
                               if (!json.status) {
                                   return false;
                               }
                               else {
                                   return true;
                               }
                           }
                       });
                   }
               }
            }
         });
    }

    data_selection = function(selected_layer, selected_sp) {
        let show_list = new Array();
        let hide_list = new Array();

        $('#layer_selector option').each(function() {
            let layer = $(this).val()
            if (layer == selected_layer) {
                for (var i=0; i < layer_group_list[layer].length; i++) {
                    show_list.push(layer_group_list[layer][i])
                }
            }
            else {
                for (var i=0; i < layer_group_list[layer].length; i++) {
                    hide_list.push(layer_group_list[layer][i])
                }
            }
        })

        $('#sp_selector option').each(function() {
            let sp = $(this).val()
            if (sp != selected_sp) {
                for (var i=0; i < stress_period_group_list[sp].length; i++) {
                    hide_list.push(stress_period_group_list[sp][i])
                }
                if (no_layer_group_list.length >0) {
                    for (var i=0; i < no_layer_group_list[sp].length; i++) {
                        hide_list.push(no_layer_group_list[sp][i])
                    }
                }
            }
            else {
                if (no_layer_group_list.length >0) {
                    for (var i=0; i < no_layer_group_list[sp].length; i++) {
                        show_list.push(no_layer_group_list[sp][i])
                    }
                }
            }
        })
        ATCORE_MAP_VIEW.show_layers(show_list)
        ATCORE_MAP_VIEW.hide_layers(hide_list)
    }

    function get_csrf_token() {
        var cookieValue = null;
        var name = 'csrftoken';
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = $.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }


	/************************************************************************
 	*                        DEFINE PUBLIC INTERFACE
 	*************************************************************************/
	/*
	 * Library object that contains public facing functions of the package.
	 * This is the object that is returned by the library wrapper function.
	 * See below.
	 * NOTE: The functions in the public interface have access to the private
	 * functions of the library because of JavaScript function scope.
	 */
	m_public_interface = {
	    init_flow_path_creation: init_flow_path_creation,
	    remove_temporary_layers: remove_temporary_layers,
	    add_pump_impact_row: add_pump_impact_row,
	    run_pump_impact_tool: run_pump_impact_tool,
	    cancel_job: cancel_job,
	};

	/************************************************************************
 	*                  INITIALIZATION / CONSTRUCTOR
 	*************************************************************************/

	// Initialization: jQuery function that gets called when
	// the DOM tree finishes loading
	$(function() {
	    setup_modpath_select();
	    init_model_publication_link();
	    init_results_tab();
	    init_tools_tab();
	    init_slide_sheet();
	    location_pump_impact();
	    delete_row_pump_impact();
	    bind_alert_close();
	    show_alert();
	    init_layer_name_change();
	    init_remove_layer();
	    init_well_upload();
	    init_public_toggle();
	    init_modal_pagination();
	    init_help_modal();
	    bind_help_modal_check();
	    init_legend_layer_data();
	    init_solution_legend_display();
	    group_layers_and_sp();
	    bind_selector();
	    flow_path_listener();
//	    $('#help-modal').modal('show');
	    $(document).on('click', '.rename-action', function(e) {
            var layer_name = $(this).parent().parent().parent().parent().find('.flatmark').find('.layer-visibility-control').data('layer-name')
            if (!layer_name) {
                return
            }
            var group_name = $(this).parent().parent().parent().parent().find('.flatmark').find('.layer-visibility-control').attr('name')
            var csrf_token = get_csrf_token();
            $('#do-action-button').on('click', function() {
                var new_name = $("#new-name-field").val()
                $.ajax({
                    type: 'POST',
                    url: window.location.href,
                    data: {'layer_name': layer_name,
                           'group_name': group_name,
                           'new_name': new_name,
                           'method': 'layer_name_change'},
                    beforeSend: xhr => {
                        xhr.setRequestHeader('X-CSRFToken', csrf_token);
                    },
                }).done(function (data) {

                })
            })
	    })

	    $.fn.inputFilter = function(inputFilter) {
            return this.on("input keydown keyup mousedown mouseup select contextmenu drop", function() {
              if (inputFilter(this.value)) {
                this.oldValue = this.value;
                this.oldSelectionStart = this.selectionStart;
                this.oldSelectionEnd = this.selectionEnd;
              } else if (this.hasOwnProperty("oldValue")) {
                this.value = this.oldValue;
                this.setSelectionRange(this.oldSelectionStart, this.oldSelectionEnd);
              }
            });
        };

        $("#flow_path_depth").inputFilter(function(value) {
            return /^\d*$/.test(value) && (value === "" || parseInt(value) <= 99999);
        });

        $('[data-toggle="tooltip"]').tooltip({
            trigger : 'hover'
        })

        $('input[type="file"]').change(function(e){
            var fileName = e.target.files[0].name;
            $("#pump-file-upload-text").text(fileName)
        });
    })

	return m_public_interface;

}()); // End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed.