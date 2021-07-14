/*****************************************************************************
 * FILE:    model_selection_map_view.js
 * DATE:    February 6, 2019
 * AUTHOR:  Corey Krewson
 * COPYRIGHT: (c) Aquaveo 2019
 * LICENSE:
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

var MODEL_SELECTION_MAP_VIEW = (function() {
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

    // help modal
    var bind_help_modal_check, init_help_modal;

	/************************************************************************
 	*                    PRIVATE FUNCTION DECLARATIONS
 	*************************************************************************/
 	// Config
 	var setup_model_select;

 	/************************************************************************
 	*                    PRIVATE FUNCTION IMPLEMENTATIONS
 	*************************************************************************/
    // Config

    setup_model_select = function() {
        // Get handle on map
	    m_map = TETHYS_MAP_VIEW.getMap();

	    // Setup layer map
	    m_layers = {};

	    // Get id from tethys_data attribute
	    m_map.getLayers().forEach(function(item, index, array) {
	        if ('tethys_data' in item && 'layer_id' in item.tethys_data) {
	           if (item.tethys_data.layer_id in m_layers) {
	               console.log('Warning: layer_id already in layers map: "' + item.tethys_data.layer_id + '".');
	           }
	           m_layers[item.tethys_data.layer_id] = item;
	        }
	    });
    };

    init_help_modal = function() {
        let show_helper = $('#show_helper_status').data('value')
        if (show_helper == 'True') {
            $('#help-modal').modal('show');
        }
    }

    bind_help_modal_check = function () {
        $('#modal-show-again').change(function() {
            // Update django session.
            var csrf_token = get_csrf_token();
            $.ajax({
                type: 'get',
                url: '/apps/modflow/update-help-modal-status/',
                data: {'status': !this.checked,
                       'page_name': 'model_selection'},
                beforeSend: xhr => {
                    xhr.setRequestHeader('X-CSRFToken', csrf_token);
                },
            }).done(function (json) {
                if(json.success) {
                }


            })
        })
    }

    ATCORE_MAP_VIEW.action_button_generator(function(feature) {
        let layer_name = ATCORE_MAP_VIEW.get_layer_name_from_feature(feature);
        let fid = ATCORE_MAP_VIEW.get_feature_id_from_feature(feature);

        // Check if layer is plottable
        let layer = m_layers[layer_name];
        let resource_id = m_layers[layer_name]['tethys_data']['layer_variable'];
        if (!layer || !layer.tethys_data.has_action) {
            return;
        }

        // Build Action Button Markup
        let action_button =
            '<div class="action-btn-wrapper">' +
                '<a class="btn btn-primary btn-popup" ' +
                    'href="/apps/modflow/' + resource_id + '/map" ' +
                    'role="button"' +
                    'data-feature-id="' + fid +'"' +
                    'data-layer-id="' + layer_name + '"' +
                    'id="map-view-plot-button"' +
                '>Load Model</a>' +
            '</div>';

        return action_button;
    })

    ATCORE_MAP_VIEW.plot_button_generator(function(feature) {
    })

    ATCORE_MAP_VIEW.properties_table_generator(function(feature) {
    })

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
	};

	/************************************************************************
 	*                  INITIALIZATION / CONSTRUCTOR
 	*************************************************************************/

	// Initialization: jQuery function that gets called when
	// the DOM tree finishes loading
	$(function() {
	    setup_model_select();
	    init_help_modal();
	    bind_help_modal_check();
	});

	return m_public_interface;

}()); // End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed.