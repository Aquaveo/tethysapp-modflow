                                                   /*****************************************************************************
 * FILE:    spatial_data_mwv.js
 * DATE:    March 5, 2019
 * AUTHOR:  Nathan Swain
 * COPYRIGHT: (c) Aquaveo 2019
 * LICENSE:
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

var SPATIAL_DATA_MWV = (function() {
	// Wrap the library in a package function
	"use strict"; // And enable strict mode for this library

	/************************************************************************
 	*                      MODULE LEVEL / GLOBAL VARIABLES
 	*************************************************************************/
 	// Module variables
 	var m_public_interface;				// Object returned by the module

 	var m_map;                          // OpenLayers map object

 	var m_data_popup_overlay,          // OpenLayers overlay containing the spatial data popup
        m_$data_popup_container,       // Spatial data popup container element
        m_$data_popup_content,         // Spatial data popup content element
        m_$data_popup_closer,          // Spatial data popup close button
        m_data_popup_loading_gif;      // Loading gif content
    // Constant
    var well_input_name = "DiversionInput";
	/************************************************************************
 	*                    PRIVATE FUNCTION DECLARATIONS
 	*************************************************************************/
    var setup_map;

    var init_data_popup, on_select_features, show_spatial_data_pop_up, hide_spatial_data_pop_up,
        reset_spatial_data_pop_up, save_data, after_form_load;

    var disable_start_duration_field, enable_start_duration_field;
 	/************************************************************************
 	*                    PRIVATE FUNCTION IMPLEMENTATIONS
 	*************************************************************************/

    // Setup Map
    setup_map = function() {
        // Get handle on map
	    m_map = TETHYS_MAP_VIEW.getMap();
    };

    init_data_popup = function() {
        m_$data_popup_container = $('#spatial-data-popup');
        m_$data_popup_content = $('#spatial-data-form');
        m_$data_popup_closer = $('#spatial-data-popup-close-btn');
        m_data_popup_loading_gif = m_$data_popup_content.html();

        // Handle closer click events
        m_$data_popup_closer.on('click', function() {
            hide_spatial_data_pop_up();
            return false;
        });

        // Unset Display None
        m_$data_popup_container.css('display', 'none');

    };

    show_spatial_data_pop_up = function(selected) {
    };

    hide_spatial_data_pop_up = function() {
        m_$data_popup_container.css('display', 'none');
        m_$data_popup_closer.blur();
    };

    reset_spatial_data_pop_up = function() {
        hide_spatial_data_pop_up();
        m_$data_popup_content.html(m_data_popup_loading_gif);
    };

    save_data = function() {
        let $saf = $(m_$data_popup_content);
        let data = $saf.serialize();
        data = data + '&method=' + 'save-spatial-data';
        let csrf_token = get_csrf_token()
        $.ajax({
            type: 'POST',
            url: window.location.href,
            data: {'data': data,
                   'method': 'save_spatial_data'},
            beforeSend: xhr => {
                xhr.setRequestHeader('X-CSRFToken', csrf_token);
            },
        }).done(function (data) {
            if (data['success'] == true) {
                $('#' + well_input_name + data['feature_id']).val(data['time_series'])
                $('#' + well_input_name + data['feature_id']).val(data['time_series'])
                $('#' + well_input_name + data['feature_id']).val(data['time_series'])
                disable_start_duration_field(data['feature_id'])
                hide_spatial_data_pop_up();
            }
            else {
                hide_spatial_data_pop_up();
            }
        });

    };

    disable_start_duration_field = function(feature_id) {
        $('#StartTime' + feature_id).prop('disabled', true);
        $('#StartTime' + feature_id).prop('placeholder', 'Use Pumping Schedule');
        $('#Duration' + feature_id).prop('disabled', true);
        $('#Duration' + feature_id).prop('placeholder', 'Use Pumping Schedule');
    }

    enable_start_duration_field = function(feature_id) {
        $('#StartTime' + feature_id).prop('disabled', false);
        $('#StartTime' + feature_id).prop('placeholder', '');
        $('#Duration' + feature_id).prop('disabled', false);
        $('#Duration' + feature_id).prop('placeholder', '');
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


    after_form_load = function() {

    };

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
	    'save_data': save_data,
	    'after_form_load': function(func) {
	        after_form_load = func;
	    },
	    'disable_start_duration_field': disable_start_duration_field,
	    'enable_start_duration_field': enable_start_duration_field,
	};

	/************************************************************************
 	*                  INITIALIZATION / CONSTRUCTOR
 	*************************************************************************/

	// Initialization: jQuery function that gets called when
	// the DOM tree finishes loading
	$(function() {
	    // Silence warning about leaving the page during ajax requests
	    window.onbeforeunload = null;
	    var enable_spatial_data = $('#spatial-data-attributes').data('enable-spatial-data-popup');
	    if (enable_spatial_data) {
	        setup_map();
            init_data_popup();
	    }
	});

	return m_public_interface;

}()); // End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed.