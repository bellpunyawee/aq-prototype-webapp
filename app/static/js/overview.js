// Overview Page Specific JavaScript

// Global variables specific to overview page (learning path)
var cellMapping = {};
var cellFullMapping = {};
var cellTimingsMapping = {};
var cellTimes = {}; // Populated by fetchCellTimes

function initOverviewPage() {
    console.log("Initializing Overview Page specific JavaScript");

    // Initial data loading for overview components
    if (typeof fetchInitialCells === 'function') fetchInitialCells(); // For learning path
    // if (typeof getUserPath === 'function') getUserPath(); // Called by fetchInitialCells or separately
    
    // Event Handlers specific to overview_page.html
    // Start Quiz button (assuming settings are saved implicitly or not needed before starting from overview)
    $("#start_quiz_btn_QE2_OG_disclaimer").off('click').on('click', function () {
        console.log("Overview Start Quiz button clicked");
        // Assuming saveSettings() might be from settings.js and startQuiz() from quiz_logic.js
        // For now, direct call, ensure those functions are globally available when their files are created.
        if (typeof saveSettings === 'function') {
            saveSettings().then(function(status) {
                if (status === false) { // Check for explicit false if saveSettings can fail
                    console.log("Settings save failed or was aborted by saveSettings logic.");
                    // Optionally, display an alert to the user from common.js
                    // if (typeof alertCreation === 'function') alertCreation("#main_alert_point", "warning", "Could not save settings before starting quiz.", true);
                    return; 
                }
                // Proceed to start quiz only if settings save was successful (or not needed to be saved)
                if (typeof startQuiz === 'function') {
                    startQuiz();
                } else {
                    console.error("startQuiz function not found.");
                }
            }).catch(function(error) {
                console.error("Error in saveSettings promise:", error);
                // if (typeof alertCreation === 'function') alertCreation("#main_alert_point", "danger", "An error occurred while saving settings.", true);
            });
        } else {
            console.warn("saveSettings function not found, proceeding to startQuiz directly.");
            if (typeof startQuiz === 'function') {
                startQuiz();
            } else {
                console.error("startQuiz function not found.");
            }
        }
    });

    // Placeholder for Learning Path related commented-out buttons if they become active:
    // $("#reset_btn").click(function () { getUserPath(); fetchInitialCells(); });
    // $("#clear_btn").click(function () { /* ... clear logic ... */ });
    // $("#start_learning_btn").click(function () { updatePath(); /* ... last_updated logic ... */ });

    // Initialize sortable lists for learning path
    if ($("#path-list ul").length && $("#full-list ul").length) {
        $("#path-list ul, #full-list ul")
          .sortable({
            connectWith: ".reorder, .reorder-full",
            update: function () {
              if (typeof updateDisplayPath === 'function') updateDisplayPath("#path-list ul li", "cur_path");
              if (typeof calculateTotalTimeCurrentPath === 'function') calculateTotalTimeCurrentPath();
            },
          })
          .disableSelection();
    }

    // Parts of original getUserInfo relevant to overview (e.g., charts if they belong here)
    // This would call specific functions to update only overview elements.
    // For example, if learner_ability_chart and learner_score_chart are on overview:
    // fetchOverviewChartsData(); // This new function would get data and call presentChart
    console.log("Overview Page JS Initialized.");
}

// --- Learning Path Functions (moved from dashboard.js) ---

function getUserPath() {
  if (!$('#draggable_list').length && !$('#cur_path').length) return;
  $.ajax({
    type: "POST",
    url: "/req_get_user_path", // Ensure this route exists and returns expected data
    success: function (response) {
      // console.log("req_get_user_path response:", response);
      if (response.result == "success") {
        var append_string = "";
        var path = response.path || [];
        var cpath = response.cpath || [];
        if (cpath.length == 0 && path.length > 0) {
          cpath = path; // Default to recommended path if current path is empty
        }
        for (var i = 0; i < cpath.length; i++) {
          // Assuming cpath items are cell IDs. Description will be added by updatePathList
          append_string += "<li id=cell-" + cpath[i] + ">" + cpath[i] + "</li>";
        }
        if ($("#draggable_list").length) $("#draggable_list").html(append_string);
        
        // Update display path with descriptions via cellMapping
        if (typeof updateDisplayPath === 'function' && typeof cellMapping !== 'undefined') {
            updateDisplayPath("#path-list ul li", "cur_path"); // Assumes #path-list ul is #draggable_list
        } else if ($("#cur_path").length) { // Fallback to raw IDs if mapping/function not ready
            $("#cur_path").text(cpath.join(' -> '));
        }
        
        if (typeof fetchCellTimes === 'function') fetchCellTimes(path, cpath);
      }
    },
    error: function () { console.error("An error occurred while fetching the user's path."); }
  });
}

function fetchCellTimes(rpath, cpath) {
  // This function was empty in dashboard.js, assuming it might be populated elsewhere
  // or its logic was embedded in fetchInitialCells's success handler for cellTimingsMapping
  // For now, it's a placeholder. If cellTimes are fetched, they should populate the global `cellTimes` object.
  // console.log("fetchCellTimes called with rpath:", rpath, "cpath:", cpath);
  // If cellTimingsMapping is populated by fetchInitialCells, this might not need to do much.
  // Ensure `calculateTotalTimeCurrentPath` and `calculateTotalTimeRecommendedPath` can access `cellTimes`.
  // The original `fetchInitialCells` populates `cellTimingsMapping`. Let's assume `cellTimes` is an alias or should use that.
  cellTimes = cellTimingsMapping; // Make sure cellTimes has the data
  if (typeof calculateTotalTimeCurrentPath === 'function') calculateTotalTimeCurrentPath();
  if (typeof calculateTotalTimeRecommendedPath === 'function' && rpath) calculateTotalTimeRecommendedPath(rpath);
}

function calculateTotalTimeCurrentPath() {
  if (!$('#path-list ul li').length && !$('#est_time').length) return;
  var total_time = 0;
  $("#path-list ul li").each(function () {
    var cellId = $(this).attr("id").replace("cell-", "");
    if (cellTimes && cellTimes[cellId]) { // Check cellTimes is populated
      total_time += Number(cellTimes[cellId]);
    }
  });
  var hours = Math.floor(total_time / 60);
  var minutes = total_time % 60;
  var timeText = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
  $("#est_time").text(timeText);

  if ($("#time-note").length) {
    if (total_time < 150 || total_time > 210) {
      $("#est_time").removeClass("text-muted").css("color", "red");
      $("#time-note").show();
    } else {
      $("#est_time").addClass("text-muted").css("color", "");
      $("#time-note").hide();
    }
  }
}

function calculateTotalTimeRecommendedPath(rpath) {
  if (!rpath || !$('#rec_est_time').length) return;
  var total_time = 0;
  rpath.forEach(function (cellId) {
    if (cellTimes && cellTimes[cellId]) { // Check cellTimes is populated
      total_time += Number(cellTimes[cellId]);
    }
  });
  var hours = Math.floor(total_time / 60);
  var minutes = total_time % 60;
  var timeText = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
  $("#rec_est_time").text(timeText);
}

function updatePath() {
  if (!$('#path-list ul li').length) return;
  var cur_path_ids = [];
  $("#path-list ul li").each(function () {
    var cellId = $(this).attr("id").replace("cell-", "");
    cur_path_ids.push(cellId);
  });
  cur_path_ids = cur_path_ids.filter((i) => i.trim() != "").join(",");
  // console.log("Updating cur_path: ", cur_path_ids);
  $.ajax({
    method: "POST",
    url: "/update_path", // Ensure this route exists
    data: { path: cur_path_ids }, // Send as object for easier parsing on server
    cache: false,
    success: function() { /* console.log("Path updated successfully."); */ },
    error: function() { console.error("Error updating path."); }
  });
}

function fetchCells() { // Used by clear_btn (currently commented out)
  if (!$('#full-list ul').length) return;
  $.ajax({
    type: "POST",
    url: "/req_get_total_cell", // Assumes this returns all cells {result: "success", cell_list: [[id, desc, full_desc, time], ...]}
    success: function (response) {
      if (response.result === "success") {
        $("#full-list ul").empty();
        $.each(response.cell_list, function (index, cell) {
          var entry = $('<li></li>').attr('id', 'cell-' + cell[0]).attr('title', cell[2])
            .text(cell[0] + ": " + cell[1] + " (" + cell[3] + " mins)");
          $("#full-list ul").append(entry);
        });
      } else {
        console.error("Failed to fetch cell data: " + (response.status || 'Unknown error'));
      }
    },
    error: function () { console.error("An error occurred while fetching cell data."); }
  });
}

function fetchInitialCells() { // Call this on page load for overview
  if (!$('#full-list ul').length && !$('#path-list ul li').length) {
    // Only run if learning path elements exist
    // console.log("Learning path elements not found, skipping fetchInitialCells.");
    return; 
  }
  $.ajax({
    type: "POST",
    url: "/req_get_total_cell",
    success: function (response) {
      if (response.result === "success") {
        $("#full-list ul").empty();
        cellMapping = {}; // Reset global/overview-scoped vars
        cellFullMapping = {};
        cellTimingsMapping = {};

        var currentPathIds = [];
        $("#path-list ul li").each(function () {
          var cellId = $(this).attr("id").replace("cell-", "");
          currentPathIds.push(String(cellId)); // Ensure string for comparison
        });

        $.each(response.cell_list, function (index, cell) {
          var cellId = String(cell[0]);
          cellMapping[cellId] = cell[1];
          cellFullMapping[cellId] = cell[2];
          cellTimingsMapping[cellId] = cell[3];

          if (!currentPathIds.includes(cellId)) {
            var entry = $('<li></li>').attr('id', 'cell-' + cellId).attr('title', cell[2])
              .text(cellId + ": " + cell[1] + " (" + cell[3] + " mins)");
            $("#full-list ul").append(entry);
          }
        });
        
        cellTimes = cellTimingsMapping; // Populate cellTimes for calculations
        if (typeof updatePathList === 'function') updatePathList(); // Pass mappings if needed, or use global
        if (typeof getUserPath === 'function') getUserPath(); // This will call fetchCellTimes which now uses the populated cellTimes
        // if (typeof updateDisplayPath === 'function') updateDisplayPath("#path-list ul li", "cur_path"); // Called by getUserPath after list is populated
      } else {
        console.error("Failed to fetch initial cell data: " + (response.status || 'Unknown error'));
      }
    },
    error: function () { console.error("An error occurred while fetching initial cell data."); }
  });
}

function updatePathList() { // Removed mappings as params, uses global/overview scope
  $("#path-list ul li").each(function () {
    var cellId = $(this).attr("id").replace("cell-", "");
    if (cellMapping[cellId]) {
      $(this).text(
        cellId + ": " + cellMapping[cellId] + " (" + (cellTimingsMapping[cellId] || 'N/A') + " mins)"
      );
      $(this).attr("title", cellFullMapping[cellId] || '');
    }
  });
}

function updateDisplayPath(list_field, display_field) {
  if (!$('#' + display_field).length) return;
  var pathDescriptions = [];
  $(list_field).each(function () {
    var cellId = $(this).attr("id").replace("cell-", "");
    if (cellMapping && cellMapping[cellId]) { // Check cellMapping is populated
        pathDescriptions.push(cellMapping[cellId]);
    } else {
        pathDescriptions.push('Cell ' + cellId); // Fallback
    }
  });
  var arrowIcon = ' <i class="bi bi-arrow-right"></i> ';
  $('#' + display_field).html(pathDescriptions.join(arrowIcon));
}

// Placeholder for parts of getUserInfo that would populate Overview page charts
// e.g., learner_ability_chart, learner_score_chart
function fetchOverviewChartsData() {
    // This function would make an AJAX call (perhaps to /req_userinfo or a new endpoint)
    // and then use presentChart() from common.js to display the charts.
    // For now, it's a placeholder.
    // Example call structure, assuming data is fetched and in 'response' object:
    /*
    if ($('#learner_ability_chart').length && typeof presentChart === 'function') {
        presentChart("learner_ability_chart", "ability_chart_status", response.learner_ability, "My Ability Trend", [], interpretPerformance);
    }
    if ($('#learner_score_chart').length && typeof presentChart === 'function') {
        var map_data_array = [];
        if (response.score_list && response.score_list.Extrainfo) {
            for (i = 0; i < response.score_list["Data Point"].length; i++) {
                map_data_array.push(
                String(response.score_list.Extrainfo[0][i]) + "/" + String(response.score_list.Extrainfo[1][i])
                );
            }
        }
        presentChart("learner_score_chart", "score_chart_status", response.score_list, "My Score History", [], null, "", map_data_array);
    }
    */
}

// $(document).ready() specific to overview.js
$(document).ready(function() {
    if (typeof initOverviewPage === 'function') {
        initOverviewPage();
    }
});
