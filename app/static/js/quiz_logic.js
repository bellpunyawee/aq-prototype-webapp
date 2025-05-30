// Quiz Logic (for active quiz sessions like pretest, posttest, main quiz)

// Global or module-scoped variables for quiz state
var timerInterval = false;
var timestamp_stop = 0;
var last_ts_server = 0;
var selectedAnswer = null; // Stores the ID of the selected radio button for the current question

// $(document).ready() for quiz_logic.js - primarily for binding events to quiz elements
// This assumes that the quiz HTML structure (#quiz_page and its contents) is loaded when this script runs.
// If quiz UI is loaded dynamically, these bindings might need to be applied after UI is loaded,
// or use delegated event handlers from a parent static element.
$(document).ready(function() {
    // Event listener for radio buttons (answer choices)
    // Using delegated event for robustness if options are dynamically loaded into quiz_page
    $('#quiz_page').on('click', 'input[checkbox-role="choice_selector"]', function () {
        var radio = $(this);
        if (radio.data("waschecked") == true) {
            radio.prop("checked", false);
            radio.data("waschecked", false);
            selectedAnswer = null;
        } else {
            // Uncheck all others in the same group and set their waschecked to false
            $('input[name="' + radio.attr('name') + '"]').data("waschecked", false);
            radio.prop("checked", true); // Check the clicked one
            radio.data("waschecked", true);
            selectedAnswer = radio.attr("id");
        }
    });

    // Submit Button Logic
    $('#quiz_page').on('click', '#submit_btn', function () {
        if (selectedAnswer !== null) {
            if (typeof showConfirmToast === 'function') showConfirmToast();
            else console.warn("showConfirmToast not defined. Did you include common.js or a similar utility?");
        } else {
            if (typeof alertCreation === 'function') alertCreation("#quiz_alert_point", "warning", "Select one of the options to submit the answer.", true);
            else alert("Select one of the options to submit the answer.");
        }
    });
    
    // IDK Button Logic
    $('#quiz_page').on('click', '#idk_btn', function () {
        // Check if an answer is already selected. If so, user should deselect it first.
        if (selectedAnswer !== null) {
             if (typeof alertCreation === 'function') alertCreation("#quiz_alert_point", "warning", "You have selected an option. Deselect it if you don't know the answer.", true);
             else alert("You have selected an option. Deselect it if you don't know the answer.");
             return;
        }
        if (typeof showConfirmToast === 'function') showConfirmToast();
        else console.warn("showConfirmToast not defined.");
    });

    // Confirmation Toast Buttons (assuming toast is within #quiz_page or globally accessible)
    // These might need to be global if toast is not inside #quiz_page
     $('#quiz_page').on('click', '#confirmSubmitBtn', function () {
        if (bootstrap && bootstrap.Toast && document.getElementById("quizConfirmToast")) {
            bootstrap.Toast.getInstance(document.getElementById("quizConfirmToast")).hide();
        }
        var answerIndex = 0; // Default to IDK
        if (selectedAnswer !== null) { // An actual option was selected
             answerIndex = $('input[checkbox-role="choice_selector"]').index(
                           $('input[checkbox-role="choice_selector"]:checked')
                         ) + 1;
        }
        if (typeof submitAnswer === 'function') submitAnswer(answerIndex);
    });

    $('#quiz_page').on('click', '#cancelSubmitBtn', function () {
         if (bootstrap && bootstrap.Toast && document.getElementById("quizConfirmToast")) {
            bootstrap.Toast.getInstance(document.getElementById("quizConfirmToast")).hide();
        }
    });
    
    // Next question button (dynamically shown/hidden)
    $('#quiz_page').on('click', '#next_question', function() {
        if (typeof fetchQuestion === 'function') fetchQuestion();
    });
});


// Function to show confirmation toast (specific to quiz, uses #quizConfirmToast)
function showConfirmToast() {
    var toastEl = document.getElementById("quizConfirmToast");
    if (toastEl && bootstrap && bootstrap.Toast) {
        var toastElement = bootstrap.Toast.getOrCreateInstance(toastEl, { autohide: false });
        toastElement.show();
    } else {
        console.error("#quizConfirmToast element not found or Bootstrap Toast not available.");
        // Fallback if toast doesn't work:
        // var confirmed = confirm("Are you sure you want to submit your answer?");
        // if (confirmed) {
        //     var answerIndex = selectedAnswer ? ($('input[checkbox-role="choice_selector"]').index($('input[checkbox-role="choice_selector"]:checked')) + 1) : 0;
        //     if (typeof submitAnswer === 'function') submitAnswer(answerIndex);
        // }
    }
}


function startQuiz() { // Called from overview or settings page
  if (typeof loading === 'function') loading(true);
  $.ajax({
    type: "POST",
    url: "/req_start_quiz", // Server should set session['quiz_start'] = true
    success: function (response) {
      if (response.result == "success") {
        // Redirect to the page that hosts the quiz interface,
        // or fetchQuestion if current page is the quiz page
        // Assuming dashboard.html (or pretest/posttest) is where #quiz_page is.
        // If current page isn't the quiz page, a redirect might be needed.
        // For now, directly call fetchQuestion, assuming this script is loaded on a page with #quiz_page.
        if (typeof fetchQuestion === 'function') fetchQuestion();
        else console.error("fetchQuestion not defined in quiz_logic.js context");
      } else {
        if (typeof loading === 'function') loading(false);
        if (typeof alertCreation === 'function') alertCreation("#main_alert_point", "danger", response.status || "Failed to start quiz.", true);
        else alert(response.status || "Failed to start quiz.");
      }
    },
    error: function() {
      if (typeof loading === 'function') loading(false);
      if (typeof alertCreation === 'function') alertCreation("#main_alert_point", "danger", "Error starting quiz.", true);
      else alert("Error starting quiz.");
    }
  });
}

function startTimer(timestamp_start, current_ts_from_server, m_duration) {
  if (!$('#span_timer').length) return;
  last_ts_server = current_ts_from_server;
  // console.log("Starting timer. Timestamp start:", timestamp_start, "Current timestamp:", current_ts_from_server);
  if (timerInterval) clearInterval(timerInterval); // Clear existing timer
  timerInterval = setInterval(function() { updateTimerDisplay(timestamp_start); }, 1000);
}

function updateTimerDisplay(timestamp_start_arg) { // Renamed param to avoid conflict
  if (!$('#span_timer').length) {
    if (timerInterval) clearInterval(timerInterval);
    return;
  }
  var elapsed_seconds = last_ts_server - timestamp_start_arg;
  var seconds = elapsed_seconds % 60;
  var minutes = Math.floor(elapsed_seconds / 60);

  if (isNaN(seconds) || isNaN(minutes)) {
    // console.error("Timer Error: NaN detected. Seconds:", seconds, "Minutes:", minutes);
    $("#span_timer").text("Error");
    if (timerInterval) clearInterval(timerInterval);
    return;
  }
  
  seconds = String(seconds).padStart(2, "0");
  minutes = String(minutes);
  last_ts_server += 1;
  $("#span_timer").text(minutes + ":" + seconds);
  // Timeout logic for fixed duration quiz (m_duration) would go here if needed,
  // comparing elapsed_seconds to m_duration * 60.
  // The original fetchQuestion had timeout reasons.
}


function abortAttempt() {
  if (typeof loading === 'function') loading(true);
  $.ajax({
    type: "POST",
    url: "/req_abort_attempt",
    success: function (response) {
      if (response.result == "success") {
        if ($("#quiz_page").length) $("#quiz_page").addClass("d-none");
        if ($("#attempt_point").length) $("#attempt_point").text("").addClass("d-none");
        if ($("#abort_point").length) $("#abort_point").empty(); // Remove abort button
        
        if (timerInterval) clearInterval(timerInterval);
        timerInterval = false;
        timestamp_stop = 0;
        last_ts_server = 0;
        if ($("#span_timer").length) $("#span_timer").text("0:00");
        selectedAnswer = null;

        // Instead of directly manipulating tabs or calling getUserInfo,
        // redirect to overview page.
        window.location.href = "/overview_new"; // Or use url_for if passed from template
      } else {
        if (typeof loading === 'function') loading(false);
        if (typeof alertCreation === 'function') alertCreation("#main_alert_point", "danger", response.status || "Failed to abort.", true);
        else alert(response.status || "Failed to abort.");
      }
    },
    error: function() {
        if (typeof loading === 'function') loading(false);
        if (typeof alertCreation === 'function') alertCreation("#main_alert_point", "danger", "Error aborting attempt.", true);
        else alert("Error aborting attempt.");
    }
  });
}

function abortButton() { // Creates and binds the abort button
  if (!$('#abort_point').length) return;
  var abort_btn_string =
    '<button class="btn btn-danger btn m-2 text-uppercase fw-bold" id="abort_btn">Abort this attempt <i class="bi bi-x-circle-fill"></i></button>';
  $("#abort_point").html(abort_btn_string);

  $("#abort_btn").off('click').on("click", function () {
    if (confirm("Cancel the attempt? This will erase all current progress.")) {
      if (typeof abortAttempt === 'function') abortAttempt();
    }
  });
}

function fetchQuestion(fetch_time_out = false) {
  if (typeof loading === 'function') loading(true);
  
  // Reset selection visual state
  if ($('input[checkbox-role="choice_selector"]').length) {
    $('input[checkbox-role="choice_selector"]').prop("checked", false).data("waschecked", false);
    selectedAnswer = null;
  }

  // Hide report, non-session areas; show quiz relevant areas
  if ($("#report").length) $("#report").addClass("d-none");
  if ($("#non-session").length) $("#non-session").addClass("d-none"); // If overview elements are in #non-session
  // Header text might be shown or hidden based on quiz context
  // if ($("#header_text").length) $("#header_text").removeClass("d-none");
  // if ($("#welcome_text").length) $("#welcome_text").addClass("d-none");
  // if ($("#adt_text").length) $("#adt_text").removeClass("d-none");
  if ($("#attempt_point").length) $("#attempt_point").removeClass("d-none");


  $.ajax({
    type: "POST",
    url: "/req_fetch_question", // This is for main quiz, pretest uses /req_fetch_pre_quiz
    data: JSON.stringify({ timeout: fetch_time_out }),
    contentType: "application/json; charset=utf-8",
    dataType: "json",
    success: function (response) {
      if (typeof loading === 'function') loading(false);
      if (response.result == "success") {
        if (response.question == "") { // Quiz ended or error
          if (typeof abortButton === 'function' && $("#abort_point").length) $("#abort_point").empty(); // Remove abort button
          if (timerInterval) clearInterval(timerInterval); // Stop timer

          var alertMsg = "Quiz ended.";
          if (response.reason == "no_quiz") alertMsg = "You have completed all available knowledge units. Congratulations!";
          else if (response.reason == "complete") alertMsg = "Quiz completed! View your results.";
          else if (response.reason == "timeout") alertMsg = "Time is up! View your results.";
          else alertMsg = "No more questions available or error encountered.";
          
          if (typeof alertCreation === 'function') alertCreation("#quiz_alert_point", "info", alertMsg, true);
          else alert(alertMsg);

          // Redirect to a report/summary page or overview.
          // For now, let's assume fetchReport is available and relevant (e.g. this is main quiz, not pre/post)
          // The route /report-history_new is for the dedicated report page.
          if (response.reason !== "no_quiz") { 
             window.location.href = "/report-history_new"; // Or appropriate summary page
          } else {
             window.location.href = "/overview_new"; // Default redirect
          }

        } else { // Display question
          if ($("#quiz_page").length) $("#quiz_page").removeClass("d-none"); else return; // Critical element

          if (typeof abortButton === 'function') abortButton(); // Add/rebind abort button

          $("#question_text").text(response.question);
          $("#question_number").text(response.question_no);
          $("#answer_text_1").text(response.ans_1);
          $("#answer_text_2").text(response.ans_2);
          $("#answer_text_3").text(response.ans_3);
          $("#answer_text_4").text(response.ans_4);
          
          // Reset explanation area
          if ($("#explanation_card").length) $("#explanation_card").addClass("fade").addClass("d-none"); // Ensure it's hidden
          if ($("#explanation_text").length) $("#explanation_text").text("");
          
          // Reset buttons
          $("#submit_btn").removeClass("disabled").removeClass("d-none");
          $("#idk_btn").removeClass("disabled").removeClass("d-none");
          $("#next_question").addClass("d-none").addClass("disabled");
          // $("#next_question").off("click").on("click", fetchQuestion); // Rebind, or use delegated from ready

          if (typeof createAnswerHistory === 'function' && $("#answer_history").length) {
            createAnswerHistory(response.quiz_streak, "answer_history"); // For live quiz history
          }
          if ($("#progress_span").length) $("#progress_span").text(
            String(response.quiz_streak.length) + "/" + String(response.total_quiz)
          );

          if (!timerInterval && response.m_duration && response.m_duration != 0) {
            if (typeof startTimer === 'function') startTimer(response.timestart, response.current_ts, response.m_duration);
          }
        }
      } else {
        // location.reload(); // Avoid reload, show error
        if (typeof alertCreation === 'function') alertCreation("#main_alert_point", "danger", response.status || "Failed to fetch question.", true);
        else alert(response.status || "Failed to fetch question.");
      }
    },
    error: function() {
        if (typeof loading === 'function') loading(false);
        if (typeof alertCreation === 'function') alertCreation("#main_alert_point", "danger", "Error fetching question.", true);
        else alert("Error fetching question.");
    }
  });
}


function submitAnswer(answer_choice) {
  if (typeof loading === 'function') loading(true);
  $.ajax({
    type: "POST",
    url: "/req_submit_answer", // For main quiz. Pretest uses /req_submit_pre_quiz
    data: JSON.stringify({ selected_choice: answer_choice }),
    contentType: "application/json; charset=utf-8",
    dataType: "json",
    success: function (response) {
      if (typeof loading === 'function') loading(false);
      // console.log("submitAnswer response", response);
      if (response.result == "success") {
        if ($("#result_text").length) {
            if (response.learner_feedback == "pass") {
                $("#result_text").text("Correct").css("color", "green");
            } else if (response.learner_feedback == "fail") {
                $("#result_text").text("Incorrect").css("color", "red");
            } else if (response.learner_feedback == "idk") {
                $("#result_text").text("Did not answer").css("color", "grey");
            }
        }
        
        if ($("#explanation_card").length) $("#explanation_card").removeClass("fade").removeClass("d-none"); // Show explanation
        if ($("#explanation_text").length) $("#explanation_text").text(response.explanation || "No explanation provided.");
        
        // Disable submit/idk, enable next
        $("#submit_btn").addClass("disabled").addClass("d-none");
        $("#idk_btn").addClass("disabled").addClass("d-none");
        $("#next_question").removeClass("d-none").removeClass("disabled");
        // Event handler for #next_question is delegated in $(document).ready()
      } else {
        if (typeof alertCreation === 'function') alertCreation("#quiz_alert_point", "danger", response.status || "Failed to submit answer.", true);
        else alert(response.status || "Failed to submit answer.");
      }
    },
    error: function() {
        if (typeof loading === 'function') loading(false);
        if (typeof alertCreation === 'function') alertCreation("#quiz_alert_point", "danger", "Error submitting answer.", true);
        else alert("Error submitting answer.");
    }
  });
}

// This version of createAnswerHistory is for the live quiz UI, might be different from report's one
// if icons or interactivity differs. For now, assuming it's similar to the one moved to report_history.js.
// If it's identical, it should be in common.js. If slightly different, it can stay here.
// For now, let's assume it's specific enough for quiz_logic.js if it updates #answer_history element.
function createAnswerHistory(array, append_place_id) { // Used by fetchQuestion for #answer_history
  if (!$('#' + append_place_id).length || !Array.isArray(array)) {
      if ($('#' + append_place_id).length) $('#' + append_place_id).html("<p class='text-muted small'>Answer history will appear here.</p>");
      return;
  }

  let row_max_length = 10; // Max items per row
  let append_string = "";
  
  if (array.length === 0) {
      $("#" + append_place_id).html("<p class='text-muted small'>No answers yet.</p>");
      return;
  }

  append_string += '<div class="row justify-content-center">'; // Ensure items are centered if row doesn't fill
  for (let i = 0; i < array.length; i++) {
    // if (i > 0 && i % row_max_length === 0) { // New row every X items
    //   append_string += '</div><div class="row justify-content-center">';
    // }
    // Simpler: let Bootstrap's flexbox handle wrapping by just adding cols
    
    append_string += '<div class="col-auto p-1">'; // col-auto makes columns fit content
    let iconClass = "";
    let buttonTitle = "Question " + (i + 1); // Simple title
    if (array[i] === 1) iconClass = "bi-check-circle-fill text-success";
    else if (array[i] === -1) iconClass = "bi-question-circle-fill text-secondary"; // IDK
    else iconClass = "bi-x-circle-fill text-danger"; // Incorrect
    
    // These buttons in quiz history are usually not interactive (not for reportonly)
    append_string += '<span title="' + buttonTitle + '"><i class="bi ' + iconClass + ' fs-4"></i></span>'; // fs-4 for slightly smaller icons
    append_string += '</div>';
  }
  append_string += '</div>'; // Close the final row

  $("#" + append_place_id).html(append_string);
}
