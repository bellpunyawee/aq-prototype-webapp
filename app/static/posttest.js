/* Useful variable */
var timerInterval = false;
var timestamp_stop = 0;
var last_ts_server = 0;

/* Event assignment to object */
$(document).ready(function () {
  getUserInfo();
  var selectedAnswer = null; // Temporarily store the selected answer

    // Event listener for radio buttons with choice_selector role
    $('input[checkbox-role="choice_selector"]').click(function () {
        var radio = $(this);

        if (radio.data('waschecked') == true) {
            // Deselect if already checked
            radio.prop('checked', false);
            radio.data('waschecked', false);
            selectedAnswer = null; // Reset selected answer
        } else {
            // Select the radio button
            $('input[checkbox-role="choice_selector"]').data('waschecked', false);
            radio.data('waschecked', true);
            selectedAnswer = radio.attr('id'); // Store the selected radio button's ID
        }
    });

    // Function to show confirmation toast
    function showConfirmToast() {
        var toastElement = new bootstrap.Toast(document.getElementById('quizConfirmToast'), {
            autohide: false
        });
        toastElement.show();
    }

    // Submit Button Logic
    $("#submit_btn").click(function () {
        if (selectedAnswer !== null) {
            showConfirmToast(); // Show the confirmation toast

            // Reset event listeners and reattach with current selection
            $("#confirmSubmitBtn").off('click').on('click', function () {
                bootstrap.Toast.getInstance(document.getElementById('quizConfirmToast')).hide();
                
                // Find the index of the selected radio button
                var answerIndex = $('input[checkbox-role="choice_selector"]').index($('input[checkbox-role="choice_selector"]:checked')) + 1;
                submitAnswer(answerIndex); // Submit the correct answer index
            });

            // Cancel Submission
            $("#cancelSubmitBtn").off('click').on('click', function () {
                bootstrap.Toast.getInstance(document.getElementById('quizConfirmToast')).hide();
            });
        } else {
            alert("Select one of the options to submit the answer.");
        }
    });

    // IDK Button Logic
    $("#idk_btn").click(function () {
        if (selectedAnswer === null) {
            showConfirmToast(); // Show the confirmation toast

            // Reset event listeners and reattach with IDK logic
            $("#confirmSubmitBtn").off('click').on('click', function () {
                bootstrap.Toast.getInstance(document.getElementById('quizConfirmToast')).hide();
                submitAnswer(0); // Submit "I don't know"
            });

            // Cancel Submission
            $("#cancelSubmitBtn").off('click').on('click', function () {
                bootstrap.Toast.getInstance(document.getElementById('quizConfirmToast')).hide();
            });
        } else {
            alert("You have selected an option. Deselect it if you don't know the answer.");
        }
    });
});

/* Overview and main functionality */
function getUserInfo() {
  thisAjax();

  function thisAjax() {
    $.ajax({
      type: "POST",
      url: "/req_userinfo_post",
      success: function (response) {
        if (response.result == "success") {
          if (response.pretest_done == true) {
            if (response.pretest_start == true) {
              loading(true);
              fetchQuestion();
            } else {
              startQuiz();
            }
          } else {
            // Redirect back
            window.location.pathname = "/launch_3/" + launchId +"/";

          }
        } else {
          alert(response.status);
        }
      },
    });
  }
}

function startQuiz() {
  loading(true);
  thisAjax();

  function thisAjax() {
    $.ajax({
      type: "POST",
      url: "/req_start_post_quiz",
      success: function (response) {
        if (response.result == "success") {
          fetchQuestion();
        } else {
          console.log(response.status);
        }
      },
    });
  }
}

/* Changed to Time Elapse */
function startTimer(timestamp_start, current_ts, m_duration) {
  last_ts_server = current_ts;
  console.log(
    "Starting timer. Timestamp start:",
    timestamp_start,
    "Current timestamp:",
    current_ts
  );
  timerInterval = setInterval(() => dummyTimer(timestamp_start), 1000);
}

function dummyTimer(timestamp_start) {
  updateTimer(timestamp_start, true);
}

function updateTimer(timestamp_start, timeout = false) {
  var elapsed_seconds = last_ts_server - timestamp_start;
  console.log(
    "Updating timer. Elapsed seconds:",
    elapsed_seconds,
    "Last timestamp server:",
    last_ts_server,
    "Timestamp start:",
    timestamp_start
  );

  var seconds = elapsed_seconds % 60;
  var minutes = Math.floor(elapsed_seconds / 60);

  if (isNaN(seconds) || isNaN(minutes)) {
    console.error(
      "Error: NaN detected. Seconds:",
      seconds,
      "Minutes:",
      minutes
    );
  } else {
    seconds = String(seconds).padStart(2, "0");
    minutes = String(minutes);

    last_ts_server += 1;

    $("#span_timer").text(minutes + ":" + seconds);
  }
}

function fetchQuestion(fetch_time_out = false) {
  loading(true);
  $("#check_").prop("checked", false);
  $('input[checkbox-role="choice_selector"]').each(function () {
    $(this).prop("checked", false);
  });

  thisAjax(fetch_time_out);

  function thisAjax(fetch_time_out) {
    $.ajax({
      type: "POST",
      url: "/req_fetch_post_quiz",
      data: JSON.stringify({ timeout: fetch_time_out }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function (response) {
        if (response.result == "success") {
          if (response.question == "") {
            if (response.pretest_done == true) {
              alertCreation(
                "#quiz_alert_point",
                "success",
                "Pretest completed, redirect back to homepage",
                true
              );
              window.location.pathname = "/launch_3/" + launchId +"/"; // New Page for QE2 : Direct learners to blank page after completed pre-quiz
            } else {
              startQuiz();
            }
          } else {
            $("#question_text").text(response.question);
            $("#question_number").text(response.question_no);
            $("#answer_text_1").text(response.ans_1);
            $("#answer_text_2").text(response.ans_2);
            $("#answer_text_3").text(response.ans_3);
            $("#answer_text_4").text(response.ans_4);
            $('span[useFor="result_text"]').each(function () {
              $(this).text("");
              $(this).css("color", "");
            });

            $("#explanation_card").addClass("fade");
            $("#explanation_text").text("");
            $("#show_exp_btn").addClass("disabled");
            $("#submit_btn").removeClass("disabled");
            $("#idk_btn").removeClass("disabled");
            $("#submit_btn").removeClass("d-none");
            $("#idk_btn").removeClass("d-none");
            $("#next_question").off("click", fetchQuestion);
            $("#next_question").addClass("d-none");
            $("#next_question").addClass("disabled");
            createAnswerHistory(response.quiz_streak, "answer_history");
            $("#progress_span").text(
              String(response.quiz_streak.length) +
                "/" +
                String(response.total_quiz)
            );
            if (!timerInterval) {
              // Timer interval has not been assigned
              if (response.m_duration != 0) {
                startTimer(
                  response.timestart,
                  response.current_ts,
                  response.m_duration
                );
                updateTimer(); // Use this to simultaneously get timer.
              }
            }
          }
          loading();
        } else {
          location.reload();
          alert(response.status);
        }
      },
    });
  }
}

function submitAnswer(answer_choice) {
  loading(true);
  thisAjax(answer_choice);

  function thisAjax(answer_choice) {
    $.ajax({
      type: "POST",
      url: "/req_submit_post_quiz",
      data: JSON.stringify({ selected_choice: answer_choice }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function (response) {
        loading();
        if (response.result == "success") {
          if (response.learner_feedback == "pass") {
            $("#result_text").text("Correct");
            $("#result_text").css("color", "green");
          } else if (response.learner_feedback == "fail") {
            $("#result_text").text("Incorrect");
            $("#result_text").css("color", "red");
          } else if (response.learner_feedback == "idk") {
            $("#result_text").text("Did not answer");
            $("#result_text").css("color", "grey");
          }
          $('span[useFor="result_text"]').each(function (context) {
            if (context + 1 == answer_choice) {
              if (response.learner_feedback == "pass") {
                $(this).text("Correct");
                $(this).css("color", "green");
              } else if (response.learner_feedback == "fail") {
                $(this).text("Incorrect");
                $(this).css("color", "red");
              } else if (response.learner_feedback == "idk") {
                $(this).text("Did not answer");
                $(this).css("color", "grey");
              }
            }
          });

          $("#explanation_card").removeClass("fade");
          $("#explanation_text").text(response.explanation);
          $("#submit_btn").addClass("disabled");
          $("#idk_btn").addClass("disabled");
          $("#submit_btn").addClass("d-none");
          $("#idk_btn").addClass("d-none");
          $("#next_question").removeClass("d-none");
          $("#next_question").removeClass("disabled");
          $("#next_question").on("click", fetchQuestion);
          $("#show_exp_btn").removeClass("disabled");
          $("#show_exp_btn").addClass("collapsed");
          $("#show_exp_btn").attr("aria-expanded", false);
          $("#explanation_box").removeClass("show");
        } else {
          alert(response.status);
        }
      },
    });
  }
}

function createAnswerHistory(array, append_place) {
  row_max_length = 10;
  append_string = "";
  row_started = false;

  total_length =
    array.length + (row_max_length - (array.length % row_max_length)); // Total number

  for (i = 0; i < total_length; i++) {
    if (i == 0 || i % 10 == 0) {
      // 1, 11, 21, 31, ...
      if (row_started == false) {
        append_string += '<div class="row">';
        row_started = true;
      }
    }

    if (i < array.length) {
      if (array[i] == 1) {
        // Success
        append_string += '<div class="col p-3">';
        append_string +=
          '<button class="btn" useFor="reportonly" title="' +
          String(i + 1) +
          '"><i class="bi bi-check-circle-fill text-success fs-1"></i></button>' +
          "</div>";
      } else if (array[i] == -1) {
        // IDK
        append_string += '<div class="col p-3">';
        // append_string += "<button class=\"btn btn-secondary btn-circle text-center\" useFor=\"reportonly\" title=\"" +String(i+1) + "\">" + String(i+1) + ">?</button>" + "</div>"
        append_string +=
          '<button class="btn" useFor="reportonly" title="' +
          String(i + 1) +
          '"><i class="bi bi-question-circle-fill text-secondary fs-1"></i></button>' +
          "</div>";
      } // Danger
      else {
        append_string += '<div class="col p-3">';
        append_string +=
          '<button class="btn" useFor="reportonly" title="' +
          String(i + 1) +
          '"><i class="bi bi-x-circle-fill text-danger fs-1"></i></button>' +
          "</div>";
      }
    } else {
      append_string += '<div class="col p-3" useFor="reportonly">';
      append_string +=
        '<button class="btn btn-link rounded-circle disabled"></button></div>';
      //append_string += "<div class=\"col\">&nbsp;</div>"
    }

    if (i % 10 == 9) {
      // 10, 20, 30, 40, ...
      if (row_started == true) {
        append_string += "</div>";
        row_started = false;
      }
    }
  }

  $("#" + append_place).html(append_string);
}
