// Report & Attempt History Page Specific JavaScript

var selected_attempt_number = 1; // Default to showing the first available attempt details initially

// Initializer for the report history page
function initReportHistoryPage() {
    console.log("Initializing Report History Page specific JavaScript");

    // Check for necessary elements before proceeding
    if (!$('#report_time').length && !$('#attempt_score_chart').length && !$('#attempt_tab').length) {
        // console.log("Required report elements not found, deferring full report initialization.");
        // return; // Or perhaps just fetch minimal data if some elements are always present
    }

    // Fetch report data when the page loads/initializes
    if (typeof fetchReport === 'function') {
        fetchReport(); // This function populates charts and attempt tabs
    } else {
        console.error("fetchReport function not found.");
    }

    // Event Handlers specific to report_history_page.html
    // Click handler for dynamically created .tablinks (for attempt history)
    // This needs to be a delegated event if .tablinks are added dynamically by createAttemptTab
    $(document).off('click', '.tablinks').on('click', '.tablinks', function () {
        // Remove 'active' class from all tabs within this specific tab system
        $('#attempt_tab .tablinks').removeClass('active'); // Scope to #attempt_tab
        $(this).addClass('active');
        const attemptNumber = $(this).data("attempt");
        // console.log("Attempt Tab clicked, Attempt Number: ", attemptNumber);
        if (typeof selectAttempt === 'function') {
            selectAttempt(attemptNumber);
        } else {
            console.error("selectAttempt function not found.");
        }
    });
    
    // Query submission (if #query_submit_btn and #query_msg exist on this page)
    if ($('#query_submit_btn').length && $('#query_msg').length) {
        $('#query_submit_btn').off('click').on('click', function() {
            if (typeof submitQuery === 'function') {
                submitQuery();
            } else {
                console.error("submitQuery function not found.");
            }
        });
    }
    
    // Retake quiz button (if #retake_quiz_btn exists and is relevant on this page)
    // The original #retake_quiz_btn handler navigated to a tab. This would now navigate to a page.
    if ($('#retake_quiz_btn').length) {
        $('#retake_quiz_btn').off('click').on('click', function() {
            // This should ideally navigate to the overview page or quiz start page
            // For now, assuming overview_page.html is the target via its route
            if (typeof overview_new === 'function') { // Check if route function name is accessible
                 window.location.href = "{{ url_for('overview_new') }}"; // This Jinja won't work in .js
                 // Better to use direct path or have path passed from template
                 console.warn("Redirection for retake quiz needs a proper URL.");
                 window.location.href = "/overview_new"; // Example direct path
            } else {
                 console.error("Overview page route function name not known for retake quiz button.");
            }
        });
    }

    // Explanation buttons (if this page structure for reportonly buttons is used)
    // This should be a delegated event if buttons are created dynamically
    $(document).off('click', 'button[useFor="reportonly"]').on('click', 'button[useFor="reportonly"]', function() {
        if ($('#history_exp_card').length && typeof getExplanation === 'function') {
            $('#history_exp_card').removeClass('d-none'); // Ensure explanation card is visible
            getExplanation($(this).attr('title')); // Pass the question number (title attribute)
            if ($('#question_id').length) {
                 $('#question_id').html(" " + $(this).attr('title'));
            }
        } else {
            console.error("Required elements for getExplanation not found.");
        }
    });
    console.log("Report History Page JS Initialized.");
}


// --- Report & History Functions (moved and adapted from dashboard.js) ---

// Fetches and displays main report data, including charts and attempt tabs
function fetchReport(switch_page = false) { // switch_page might be mostly obsolete here
  // console.log("fetchReport called on report_history_page.js");
  $.ajax({
    type: "POST",
    url: "/req_fetch_report_score", // This endpoint provides data for charts and attempts
    success: function (response) {
      if (response.result == "success") {
        // console.log("fetchReport response: ", response);
        if ($("#retake_quiz_btn").length) $("#retake_quiz_btn").removeClass("disabled");

        // Populate Attempt Summary card
        if ($("#report_time").length) {
            var seconds = response.total_second_used % 60;
            seconds = String(seconds).padStart(2, '0');
            var minutes = String(Math.floor(response.total_second_used / 60));
            $("#report_time").val(minutes + ":" + seconds + " mins");
        }
        if ($("#report_correct").length) $("#report_correct").val(response.total_correct_ans);
        if ($("#report_num_quiz").length) $("#report_num_quiz").val(response.total_quiz);
        if ($("#selected_cell").length && response.cell_index) {
            var sorted_cells = response.cell_index.sort(function (a, b) { return a - b; });
            $("#selected_cell").val(sorted_cells.join(", "));
        }

        // Charts (assuming 'attempt_chart' and 'attempt_score_chart' are on report_history_page.html)
        // The original `getUserInfo` called presentChart for 'learner_ability_chart' and 'learner_score_chart'.
        // `fetchReport` in `dashboard.js` called presentChart for 'attempt_chart' and 'attempt_score_chart'.
        // We need to ensure the correct chart IDs and data sources are used here.
        // The response from /req_fetch_report_score contains `response.score_list` (for attempt_score_chart)
        // and `response.learner_ability` (which was used for learner_ability_chart, maybe for attempt_chart too?)

        var data_label_ability = (response.learner_ability && response.learner_ability["Data Point"] && response.learner_ability["Data Point"].length <= 1) ? ["Current"] : ["Previous", "Current"];
        if (typeof presentChart === 'function' && $('#attempt_chart').length) { // Assuming learner_ability for 'attempt_chart'
            presentChart("attempt_chart", "attempt_chart_status", response.learner_ability, "Ability Level Trend", data_label_ability, interpretPerformance, "Ability Level");
        }
        
        if (typeof presentChart === 'function' && $('#attempt_score_chart').length && response.score_list) {
            var map_data_array = [];
            if (response.score_list.Extrainfo && response.score_list.Extrainfo[0] && response.score_list.Extrainfo[1]) {
                for (var i = 0; i < response.score_list["Data Point"].length; i++) {
                    map_data_array.push(
                        String(response.score_list.Extrainfo[0][i]) + "/" + String(response.score_list.Extrainfo[1][i])
                    );
                }
            }
            // Percentage conversion for display
            let percentageDataPoints = [];
            if (response.score_list["Data Point"] && response.score_list.Extrainfo && response.score_list.Extrainfo[0] && response.score_list.Extrainfo[1]) {
                for (let i = 0; i < response.score_list["Data Point"].length; i++) {
                    let dataPoint = response.score_list["Extrainfo"][0][i];
                    let extrainfoTotal = response.score_list["Extrainfo"][1][i]; // Renamed to avoid conflict
                    if (extrainfoTotal !== 0) {
                        let percentage = (dataPoint / extrainfoTotal) * 100;
                        percentageDataPoints.push(Math.round(percentage));
                    } else {
                        percentageDataPoints.push(0);
                    }
                }
            }
            // Create a copy of score_list to modify for chart if necessary
            var chartScoreList = JSON.parse(JSON.stringify(response.score_list));
            chartScoreList["Data Point"] = percentageDataPoints;

            presentChart("attempt_score_chart", "attempt_chart_status_score", chartScoreList, "Score History (%)", [], null, "", map_data_array);
        }

        // Attempt History Tabs and Content
        if (typeof createAttemptTab === 'function') createAttemptTab(response.n_attempt, "attempt_tab");
        // createAnswerHistory is called by selectAttempt after tabs are created.
        
        // Update other general info if elements exist
        if ($("#attempt_report_ans").length && typeof selected_attempt_number !== 'undefined') {
             // selectAttempt will handle this based on the default active tab
        }
        if ($("#text_box_tbd").length) $("#text_box_tbd").text(response.textboxdata || "No feedback available.");

      } else {
        if (typeof alertCreation === 'function') alertCreation("#main_alert_point", "danger", response.status || "Failed to fetch report data.", true);
        else alert(response.status || "Failed to fetch report data.");
      }
    },
    error: function() {
        if (typeof alertCreation === 'function') alertCreation("#main_alert_point", "danger", "Error fetching report data.", true);
        else alert("Error fetching report data.");
    }
  });
}

function submitQuery() {
  if (!$('#query_msg').length || !$('#query_alert_point').length) return;
  var query_msg = $("#query_msg").val();
  if (query_msg == "") {
    if (typeof alertCreation === 'function') alertCreation("#query_alert_point", "danger", "No Query entered", true);
    else alert("No Query entered");
    return;
  }
  $.ajax({
    type: "POST",
    url: "/req_submit_finish_query",
    data: JSON.stringify({ query: query_msg }),
    contentType: "application/json; charset=utf-8",
    dataType: "json",
    success: function (response) {
      if (response.result == "success") {
        if (typeof alertCreation === 'function') alertCreation("#query_alert_point", "info", response.status, true);
        else alert(response.status);
        $("#query_msg").val("");
      } else {
        if (typeof alertCreation === 'function') alertCreation("#query_alert_point", "danger", response.status, true);
        else alert(response.status);
      }
    },
    error: function() {
        if (typeof alertCreation === 'function') alertCreation("#query_alert_point", "danger", "Failed to submit query.", true);
        else alert("Failed to submit query.");
    }
  });
}

function getExplanation(answer_id) { // answer_id is actually question number in sequence for that attempt
  if (!$('#history_question_text').length) return; // Check if target elements exist
  $.ajax({
    type: "POST",
    url: "/req_get_explanation_history",
    data: JSON.stringify({
      answer_id: answer_id, // This is the question number/index for the attempt
      attempt_num: selected_attempt_number // Global var for current displayed attempt
    }),
    contentType: "application/json; charset=utf-8",
    dataType: "json",
    success: function (response) {
      if (response.result == "success") {
        $("#history_question_text").text(response.question_text || "N/A");
        $("#history_answer_text").text(response.answer_text || "N/A");
        $("#history_explanation_text").text(response.explanation_text || "N/A");
      } else {
        $("#history_question_text").text("Error loading question.");
        $("#history_answer_text").text("");
        $("#history_explanation_text").text(response.status || "Could not load explanation.");
      }
    },
    error: function () {
      $("#history_question_text").text("Error loading explanation via AJAX.");
      $("#history_answer_text").text("");
      $("#history_explanation_text").text("");
    }
  });
}

function getQuizStreak(attempt_num_for_streak) { // Renamed param to avoid confusion with global
  if (!$('#report_attempt_answer').length) return;
  $.ajax({
    type: "POST",
    url: "/req_get_quiz_streak", // This route needs to exist and return quiz_streak for the attempt
    data: JSON.stringify({ attempt_num: attempt_num_for_streak }),
    contentType: "application/json; charset=utf-8",
    dataType: "json",
    success: function (response) {
      if (response.result == "success" && typeof createAnswerHistory === 'function') {
        createAnswerHistory(response.quiz_streak, "report_attempt_answer");
        // Re-bind click for newly created buttons if not using delegated events from init
        // The current initReportHistoryPage uses delegated events, so this might not be needed here.
      } else {
        // console.log("Failed to get quiz streak: ", response.status);
        $('#report_attempt_answer').html('<p class="text-muted">Could not load answer history.</p>');
      }
    },
    error: function() {
        $('#report_attempt_answer').html('<p class="text-danger">Error fetching answer history.</p>');
    }
  });
}

function selectAttempt(attempt_num_to_select) {
  selected_attempt_number = attempt_num_to_select; // Update global
  
  if ($("#attempt_report_ans").length) {
    if (selected_attempt_number === 1) { // Assuming pre-quiz is not attempt 1 in this list.
                                        // If pre-quiz is attempt 1, logic needs to adjust.
                                        // The createAttemptTab starts from attempt 2 (index 1 for n_attempt-1)
                                        // So data-attempt on button might be actual attempt number.
      $("#attempt_report_ans").html("Attempt " + selected_attempt_number); // Or "Baseline Quiz" if attempt_num is 1
    } else {
      $("#attempt_report_ans").html("Attempt " + selected_attempt_number);
    }
  }

  if (typeof getQuizStreak === 'function') getQuizStreak(selected_attempt_number);
  
  // Fetch explanation for the first question of the selected attempt by default
  if (typeof getExplanation === 'function') getExplanation(1); 
  if ($("#question_id").length) $("#question_id").html(" 1");
  if ($("#history_exp_card").length) $("#history_exp_card").removeClass("d-none"); // Show it
}

function createAttemptTab(total_attempts, append_place_id) {
  if (!$('#' + append_place_id).length) return;
  let append_string = "";
  // Assuming total_attempts from /req_fetch_report_score is n_attempt (next attempt number)
  // So, actual attempts made are total_attempts - 1
  // Tabs should be for Attempt 1, Attempt 2, ..., Attempt (total_attempts - 2)
  // And pre-quiz if it's considered attempt 1 by the backend's get_report_data.
  // The original createAttemptTab started loop from i=1 to total_attempts (exclusive of total_attempts)
  // and data-attempt was i+1. (e.g. if total_attempts = 3 (meaning 2 attempts done), loop i=1, data-attempt=2. then i=2, data-attempt=3)
  // This seems to map to n_attempt from backend which is "next attempt to be taken"
  
  // Let's assume n_attempt from response is the total number of attempts completed + 1
  // So, if n_attempt = 1, no attempts completed yet (only prequiz maybe).
  // If n_attempt = 2, 1 attempt completed. Tab should be "Attempt 1".
  // If n_attempt = 3, 2 attempts completed. Tabs: "Attempt 1", "Attempt 2".
  
  var num_actual_attempts = total_attempts -1; // if total_attempts is "next attempt number"

  if (num_actual_attempts <= 0) {
    $('#' + append_place_id).html('<p class="text-muted">No attempts available to display.</p>');
    return;
  }

  for (let i = 1; i <= num_actual_attempts; i++) { // Loop from 1 to number of actual attempts
    let activeClass = (i === num_actual_attempts) ? " active" : ""; // Make the latest attempt active
    // Data-attempt should be the actual attempt number to fetch
    append_string +=
      '<button class="tablinks' + activeClass + '" data-attempt="' + i + '">' +
      'Attempt ' + i +
      "</button>";
  }

  $("#" + append_place_id).html(append_string);

  // Trigger click on the active tab (latest attempt) to load its data
  if ($('#' + append_place_id + ' .tablinks.active').length) {
    $('#' + append_place_id + ' .tablinks.active').trigger("click");
  } else if ($('#' + append_place_id + ' .tablinks').length) {
    // Fallback: click the first tab if no active one (shouldn't happen with above logic)
    $('#' + append_place_id + ' .tablinks:first').trigger("click");
  }
}

// This function is from dashboard.js, used by fetchReport, assuming it's for report answer history display
function createAnswerHistory(array, append_place_id) {
  if (!$('#' + append_place_id).length || !Array.isArray(array)) {
      if ($('#' + append_place_id).length) $('#' + append_place_id).html("<p>No answer history available.</p>");
      return;
  }

  let row_max_length = 10;
  let append_string = "";
  let row_started = false;
  let total_length = array.length > 0 ? array.length + (row_max_length - (array.length % row_max_length)) % row_max_length : 0;
  if (array.length === 0) total_length = 0;


  for (let i = 0; i < total_length; i++) {
    if (i % row_max_length === 0) { // Start new row
      if (row_started) append_string += '</div>'; // Close previous row if open
      append_string += '<div class="row justify-content-center">'; // Center the row content
      row_started = true;
    }

    if (i < array.length) {
      append_string += '<div class="col-auto p-1">'; // Use col-auto for tight packing, p-1 for small padding
      let iconClass = "";
      if (array[i] === 1) iconClass = "bi-check-circle-fill text-success";
      else if (array[i] === -1) iconClass = "bi-question-circle-fill text-secondary";
      else iconClass = "bi-x-circle-fill text-danger";
      append_string += '<button class="btn p-0" useFor="reportonly" title="' + (i + 1) + '"><i class="bi ' + iconClass + ' fs-3"></i></button>'; // Smaller icon
      append_string += '</div>';
    } else { // Empty placeholders for grid alignment
      append_string += '<div class="col-auto p-1"><div style="width: 2rem; height: 2rem;"></div></div>'; // Placeholder same size as button
    }

    if ((i + 1) % row_max_length === 0 || (i + 1) === total_length) { // End of row or end of items
      if (row_started) {
        append_string += "</div>";
        row_started = false;
      }
    }
  }
  if(row_started) append_string += "</div>"; // Close any unclosed row

  $("#" + append_place_id).html(append_string || "<p>No answer history available.</p>");
}


// $(document).ready() specific to report_history.js
$(document).ready(function() {
    if (typeof initReportHistoryPage === 'function') {
        initReportHistoryPage();
    }
});
