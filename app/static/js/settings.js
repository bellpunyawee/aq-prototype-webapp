// Settings Page Specific JavaScript

// Variables typically global or module-scoped for settings
var total_cell = []; // Tracks dynamically added cell selector groups
var latest_cell_box_id = 0; // Counter for unique IDs for cell selectors
var cell_indices = ""; // Holds the HTML string for cell options, populated by getTotalCellIndices
var saveSettingstatus = false; // Tracks if settings were successfully saved

// Initializer for the settings page
function initSettingsPage() {
    console.log("Initializing Settings Page specific JavaScript");

    // Populate cell_indices first, then call functions that might use it (like addCell)
    if (typeof getTotalCellIndices === 'function') {
        getTotalCellIndices(function() {
            // This callback ensures cell_indices is populated before other dependent logic runs
            // console.log("Cell indices populated, proceeding with settings setup.");
            
            // Parts of original getUserInfo relevant to populating settings form
            // This needs to be called after getTotalCellIndices if addCell depends on cell_indices
            fetchAndPopulateSettingsForm(); 
        });
    } else {
        console.error("getTotalCellIndices function not found. Settings page may not function correctly.");
        // Still try to setup basic event handlers that don't depend on cell_indices
        fetchAndPopulateSettingsForm(); // This might partially work or handle missing cell_indices
    }
    
    // Event Handlers specific to settings_page.html
    $("#setting_start_quiz_btn").off('click').on('click', function () {
        // console.log("Settings page: Save and Start Quiz button clicked");
        if (typeof saveSettings === 'function') {
            saveSettings().then(function (status) {
                if (status === true) { // Explicitly check for true if promise resolves with boolean
                    if (typeof startQuiz === 'function') {
                        startQuiz();
                    } else {
                        console.error("startQuiz function not found.");
                    }
                } else {
                    // console.log("Settings save failed or was aborted. Quiz not started.");
                    // alertCreation might be called within saveSettings on failure
                }
            }).catch(function(error){
                console.error("Error saving settings before starting quiz:", error);
            });
        } else {
            console.error("saveSettings function not found.");
        }
    });

    // Profile picture upload (if this UI is on settings_page.html)
    if ($("#show_upload").length) {
        $("#show_upload").off('click').on('click', function () {
            if ($("#upload_photo_box").hasClass("d-none")) {
                $("#upload_photo_box").removeClass("d-none");
            } else {
                $("#upload_photo_box").addClass("d-none");
            }
        });
    }
    if ($("#submit_photo_btn").length && typeof upload === 'function') {
         $("#submit_photo_btn").off('click').on('click', function (event) {
            event.preventDefault(); // Assuming it might be an anchor
            var endpoint = $(this).attr("href") || "/req_upload_profile_picture"; // Fallback endpoint
            upload("image_file", endpoint); // upload is from common.js
            if ($("#upload_photo_box").length) $("#upload_photo_box").addClass("d-none");
            if ($("#image_file").length) $("#image_file").val("");
            
            // setTimeout(getProfilePhoto, 500); // getProfilePhoto is in common.js
            // Call directly if getProfilePhoto is available
            if(typeof getProfilePhoto === 'function') {
                 setTimeout(getProfilePhoto, 500);
            }
        });
    }


    // KU Configuration: Random check button
    if ($("#random_check").length) {
        $("#random_check").off('click').on('click', function () {
            if ($(this).is(":checked")) {
                $("#random_box").removeClass("d-none");
                $("#select_box").addClass("d-none");
            } else {
                $("#select_box").removeClass("d-none");
                $("#random_box").addClass("d-none");
            }
        });
        // Trigger click to set initial state based on checkbox default
        // $("#random_check").trigger('click'); // Do this carefully, might trigger AJAX if not desired on load
    }


    // KU Configuration: Add another KU button
    if ($("#add_cell").length) {
        $("#add_cell").off('click').on('click', function (event) {
            event.preventDefault();
            if (typeof addCell === 'function') addCell();
        });
    }
    
    // Save settings button (if a separate save button exists, distinct from "Save and Start")
    // The original dashboard.js had #save_settings for this.
    if ($("#save_settings_button_id").length) { // Assuming a new ID for clarity if needed
         $("#save_settings_button_id").off('click').on('click', function() {
            if (typeof saveSettings === 'function') saveSettings();
         });
    }
    console.log("Settings Page JS Initialized.");
}

// --- Settings Specific Functions (moved or adapted from dashboard.js) ---

// Fetches initial settings values (e.g., for KU config)
function fetchAndPopulateSettingsForm() {
    // This function would be responsible for fetching user's current settings
    // (perhaps from parts of the /req_userinfo response or a new endpoint)
    // and populating the form fields on settings_page.html.
    // For example, from original getUserInfo:
    /*
    if (response.settings[1].length > 0) { // Unrandom KU selection
        if ($("#random_check").length) $("#random_check").prop("checked", false).trigger('click'); // uncheck and trigger to show select_box
        // $("#random_box").addClass("d-none"); // Handled by trigger
        // $("#select_box").removeClass("d-none"); // Handled by trigger
        
        // Clear existing dynamic cells before adding new ones
        if ($("#cell_box").length) $("#cell_box").empty(); 
        total_cell = []; // Reset tracker
        latest_cell_box_id = 0; // Reset counter

        for (var i = 0; i < response.settings[1].length; i++) {
            if (typeof addCell === 'function') addCell(true, response.settings[1][i]);
        }
    } else { // Random KU selection
        if ($("#random_check").length) $("#random_check").prop("checked", true).trigger('click');
        if ($("#cell_num").length && response.settings[0]) $("#cell_num").val(response.settings[0]);
    }
    // Max limit is passed from Flask route directly to settings_page.html, so not set here via JS
    */
   // The above is an example. The actual data might come from a dedicated part of getUserInfo or a new AJAX call.
   // For now, we assume that if global `cachedUserInfo` exists (set by common.js):
   if (typeof cachedUserInfo !== 'undefined' && cachedUserInfo && cachedUserInfo.settings) {
        const settings = cachedUserInfo.settings;
        if (settings[1] && settings[1].length > 0) { // Non-random
            if ($("#random_check").length) $("#random_check").prop("checked", false).trigger('click');
            if ($("#cell_box").length) $("#cell_box").empty();
            total_cell = []; 
            latest_cell_box_id = 0;
            for (let i = 0; i < settings[1].length; i++) {
                if (typeof addCell === 'function') addCell(true, settings[1][i]);
            }
        } else { // Random
            if ($("#random_check").length) $("#random_check").prop("checked", true).trigger('click');
            if ($("#cell_num").length && settings[0]) $("#cell_num").val(settings[0]);
        }
   } else {
       // console.log("User info with settings not yet available for form population or no settings data.");
       // Default behavior: ensure "random_check" state correctly shows/hides sections.
       if ($("#random_check").length) $("#random_check").triggerHandler('click'); // Use triggerHandler to avoid event cascade if not needed
   }
}


// Fetches all available "Knowledge Units" or cells to populate dropdowns
function getTotalCellIndices(callback) {
  if (cell_indices && cell_indices !== "") { // Check if already populated
    if (typeof callback === 'function') callback();
    return;
  }
  $.ajax({
    type: "POST",
    url: "/req_get_total_cell",
    success: function (response) {
      if (response.result == "success" && response.cell_list) {
        var temp_cell_indices = "";
        for (var i = 0; i < response.cell_list.length; i++) {
          temp_cell_indices +=
            '<option value="' + response.cell_list[i][0] + '">' +
            'Cell ' + response.cell_list[i][0] + ": " + response.cell_list[i][1] +
            "</option>";
        }
        cell_indices = temp_cell_indices; // Populate global/module-scoped variable
      } else {
        console.error("Failed to get total cell indices: " + response.status);
      }
      if (typeof callback === 'function') callback();
    },
    error: function() {
        console.error("Error in AJAX call to /req_get_total_cell");
        if (typeof callback === 'function') callback();
    }
  });
}

function addCell(selected_cell = false, cell_no = 0) {
  if (!$('#cell_box').length) return;
  if (!cell_indices) {
      // console.warn("cell_indices not populated yet for addCell.");
      // Optionally, call getTotalCellIndices here and defer addCell, or show error
      if (typeof alertCreation === 'function') alertCreation("#main_alert_point", "warning", "Cell data not loaded yet. Please wait and try again.", true);
      return;
  }

  latest_cell_box_id += 1;
  total_cell.push(latest_cell_box_id);
  
  // var allowedCells = [1, 2, 3, 4, 5, 18, 19, 20, 24, 25, 26, 27, 28, 29, 30]; // UAT specific
  var currentCellChoices = cell_indices; // Use the fetched and stored options
  // currentCellChoices = modifyCellChoices(currentCellChoices, allowedCells); // Apply UAT filtering if needed

  var append_string =
    '<div class="input-group mb-3" id="cell_form_' + latest_cell_box_id + '">' +
    '<label class="input-group-text" for="select_no_' + latest_cell_box_id + '"><i class="bi bi-paperclip"></i></label>' +
    '<select class="form-select" id="select_no_' + latest_cell_box_id + '" selectFor="cell_check">' +
    currentCellChoices +
    '</select>' +
    '<button class="btn btn-danger" type="button" onclick="removeCell(' + latest_cell_box_id + ')"><i class="bi bi-x-circle-fill"></i></button>' +
    '</div>';

  $("#cell_box").append(append_string);

  if (selected_cell == true && cell_no != 0) {
    // Set selected option. Value for options is cell_id.
    $("#select_no_" + latest_cell_box_id).val(cell_no);
  }
}

// UAT function to grey out non selectable cells - if needed, ensure it's defined or moved to common.js
// For now, assuming it's not strictly part of this refactor unless present in original dashboard.js
/*
function modifyCellChoices(cell_choices_html, allowedCells) {
  var parser = new DOMParser();
  var doc = parser.parseFromString("<select>" + cell_choices_html + "</select>", "text/html");
  var select = doc.querySelector("select");
  select.querySelectorAll("option").forEach(function (option) {
    if (!allowedCells.includes(parseInt(option.value))) {
      option.disabled = true;
      option.classList.add("text-muted", "bg-light");
    }
  });
  return select.innerHTML;
}
*/

function removeCell(id) {
  if ($('#cell_form_' + id).length) {
    $('#cell_form_' + id).remove();
    var index = total_cell.indexOf(id);
    if (index !== -1) {
      total_cell.splice(index, 1);
    }
  }
}

function weightedRandom() { // Used by saveSettings if num_quiz is to be randomized
  const weights = [
    { value: 3, weight: 0.6 }, { value: 4, weight: 0.3 }, { value: 5, weight: 0.1 }
  ];
  const totalWeight = weights.reduce((total, item) => total + item.weight, 0);
  const randomNum = Math.random() * totalWeight;
  let runningWeight = 0;
  for (let i = 0; i < weights.length; i++) {
    runningWeight += weights[i].weight;
    if (randomNum <= runningWeight) { return weights[i].value; }
  }
  return 3; // Fallback
}

function saveSettings() {
  return new Promise((resolve) => { // Simplified to only resolve, no reject needed for promise chain
    var num_quiz_val, num_cell_val, num_timer_val, max_limit_quiz_val; // Renamed to avoid conflict
    var random_val = $("#random_check").is(":checked");
    var cell_array_val = [];

    if (!random_val) {
      $('select[selectFor="cell_check"]').each(function () {
        cell_array_val.push($(this).val());
      });
      cell_array_val = Array.from(new Set(cell_array_val));
      num_cell_val = cell_array_val.length;
    } else {
      num_cell_val = $("#cell_num").length ? $("#cell_num").val() : 0;
    }

    num_quiz_val = 3; // Default or use weightedRandom() if that logic is reinstated
    num_timer_val = 10000; // Default timer
    max_limit_quiz_val = $("#max_limit").length ? $("#max_limit").val() : 10;

    if (num_cell_val == 0) {
      saveSettingstatus = false; // Update global status
      var alert_msg = random_val ? "At least number of cell must be 1" : "At least 1 cell must be selected";
      if (random_val && $("#cell_num").length) $("#cell_num").addClass("is-invalid");
      
      if (typeof alertCreation === 'function') alertCreation("#main_alert_point", "danger", alert_msg, true);
      else alert(alert_msg);
      resolve(false); // Resolve promise with false
      return;
    }
    
    // AJAX call to save settings
    $.ajax({
      type: "POST",
      url: "/req_save_settings",
      data: JSON.stringify({
        num_quiz: num_quiz_val,
        check_quiz: cell_array_val, // Array of selected cell IDs if not random
        num_cell: num_cell_val,     // Number of cells (either from selection or input)
        timer: num_timer_val,
        max_quiz: max_limit_quiz_val,
      }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function (response) {
        if (response.result == "success") {
          if ($("#cell_num").length) $("#cell_num").removeClass("is-invalid");
          if (typeof alertCreation === 'function') alertCreation("#main_alert_point", "success", "Settings were saved.", true);
          saveSettingstatus = true; // Update global status
          resolve(true); // Resolve promise with true
        } else {
          if (typeof alertCreation === 'function') alertCreation("#main_alert_point", "danger", response.status, true);
          else alert(response.status);
          saveSettingstatus = false;
          resolve(false);
        }
      },
      error: function () {
        if (typeof alertCreation === 'function') alertCreation("#main_alert_point", "danger", "Failed to save settings.", true);
        else alert("Failed to save settings.");
        saveSettingstatus = false;
        resolve(false);
      }
    });
  });
}

// $(document).ready() specific to settings.js
$(document).ready(function() {
    if (typeof initSettingsPage === 'function') {
        initSettingsPage();
    }
});
