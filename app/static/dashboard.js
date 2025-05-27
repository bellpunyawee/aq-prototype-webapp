/* Useful variable */
var timerInterval = false;
var timestamp_stop = 0;
var last_ts_server = 0;
var total_cell = [];
var latest_cell_box_id = 0;
var cell_indices = "";
var saveSettingstatus = false;
var selected_attempt_number = 1;
var cellTimes = {};
/* Event assignment to object */
$(document).ready(function () {
  getTotalCellIndices();
  getUserInfo();
  //getUserPath();
  fetchCellTimes([], []); //initialise rpath and cpath
  /* Chart of users mastery */
  /* Overview - Start quiz button */
  $("#disclaimer_btn").click(function () {
    // $("#tab-4").click();
    // updatePath();
    $("#tab-4").click();
  });

  $("#back_overview_btn").click(function () {
    $("#tab-1").click();
  });

  $("#back_setting_btn").click(function () {
    $("#tab-3").click();
  });

  $("#tab-1").click(function () {
    $("#welcome_text").removeClass("d-none");
    $("#adt_text").addClass("d-none");
  });
  $("#tab-2").click(function () {
    $("#welcome_text").addClass("d-none");
    $("#adt_text").removeClass("d-none");
  });
  $("#tab-3").click(function () {
    $("#welcome_text").addClass("d-none");
    $("#adt_text").removeClass("d-none");
  });
  $("#tab-4").click(function () {
    $("#welcome_text").addClass("d-none");
    $("#adt_text").removeClass("d-none");
  });

  $("#start_quiz_btn").click(function () {
    saveSettings();
    startQuiz();
  });

  $("#start_quiz_btn_QE2_OG_disclaimer").click(function () {
    saveSettings();
    startQuiz();
  });

  $("#setting_start_quiz_btn").click(function () {
    console.log("saveSettingstatus", saveSettingstatus);
    saveSettings().then(function (status) {
      if (status == false) {
        return;
      }
      startQuiz();
    });
  });

  $("#show_upload").click(function () {
    if ($("#upload_photo_box").hasClass("d-none")) {
      $("#upload_photo_box").removeClass("d-none");
    } else {
      $("#upload_photo_box").addClass("d-none");
    }
  });

  $("#submit_photo_btn").click(function () {
    var endpoint = $(this).attr("href");
    upload("image_file", endpoint);
    $("#upload_photo_box").addClass("d-none");
    $("#image_file").val("");

    setTimeout(getProfilePhoto, 500);
  });

  /* Settings - Random check button */
  $("#random_check").click(function () {
    if ($(this).is(":checked")) {
      $("#random_box").removeClass("d-none");
      $("#select_box").addClass("d-none");
    } else {
      $("#select_box").removeClass("d-none");
      $("#random_box").addClass("d-none");
    }
  });

  /* Settings - Add another button*/
  $("#add_cell").click(function (event) {
    event.preventDefault();
    addCell();
  });

  /* Settings - save button*/
  $("#save_settings").click(function () {
    $("#setting_start_quiz_btn").removeClass("disabled");
    saveSettings();
  });

  /*$("#reset_btn").click(function () {
    getUserPath();
    fetchInitialCells();
  });

  $("#clear_btn").click(function () {
    $("#path-list ul").empty();
    document.getElementById("cur_path").innerHTML = "";
    fetchCells();
    $("#est_time").text("0m");
    $("#est_time").removeClass("text-muted").css("color", "red");
    $("#time-note").show();
  });

  // Add click event listener for the Update button
  $("#start_learning_btn").click(function () {
    updatePath(); // Call the updatePath function
    setTimeout(function () {
      // Get current date and time and format it
      let currentDate = new Date();
      let options = {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "numeric",
        hour12: true,
      };
      let formattedDate = currentDate.toLocaleString("en-US", options);
      // Display the formatted date and time in the bottom-right
      $("#last_updated").html(
        '<i class="bi bi-clock"></i> Last updated: ' + formattedDate
      );
    }, 3000); // Simulated process time (3 seconds)
  });*/

  var selectedAnswer = null; // Temporarily store the selected answer

  // Event listener for radio buttons with choice_selector role
  $('input[checkbox-role="choice_selector"]').click(function () {
    var radio = $(this);

    if (radio.data("waschecked") == true) {
      // Deselect if already checked
      radio.prop("checked", false);
      radio.data("waschecked", false);
      selectedAnswer = null; // Reset selected answer
    } else {
      // Select the radio button
      $('input[checkbox-role="choice_selector"]').data("waschecked", false);
      radio.data("waschecked", true);
      selectedAnswer = radio.attr("id"); // Store the selected radio button's ID
    }
  });

  // Function to show confirmation toast
  function showConfirmToast() {
    var toastElement = new bootstrap.Toast(
      document.getElementById("quizConfirmToast"),
      {
        autohide: false,
      }
    );
    toastElement.show();
  }

  // Submit Button Logic
  $("#submit_btn").click(function () {
    if (selectedAnswer !== null) {
      showConfirmToast(); // Show the confirmation toast

      // Reset event listeners and reattach with current selection
      $("#confirmSubmitBtn")
        .off("click")
        .on("click", function () {
          bootstrap.Toast.getInstance(
            document.getElementById("quizConfirmToast")
          ).hide();

          // Find the index of the selected radio button
          var answerIndex =
            $('input[checkbox-role="choice_selector"]').index(
              $('input[checkbox-role="choice_selector"]:checked')
            ) + 1;
          submitAnswer(answerIndex); // Submit the correct answer index
        });

      // Cancel Submission
      $("#cancelSubmitBtn")
        .off("click")
        .on("click", function () {
          bootstrap.Toast.getInstance(
            document.getElementById("quizConfirmToast")
          ).hide();
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
      $("#confirmSubmitBtn")
        .off("click")
        .on("click", function () {
          bootstrap.Toast.getInstance(
            document.getElementById("quizConfirmToast")
          ).hide();
          submitAnswer(0); // Submit "I don't know"
        });

      // Cancel Submission
      $("#cancelSubmitBtn")
        .off("click")
        .on("click", function () {
          bootstrap.Toast.getInstance(
            document.getElementById("quizConfirmToast")
          ).hide();
        });
    } else {
      alert(
        "You have selected an option. Deselect it if you don't know the answer."
      );
    }
  });

  // Handle click events for tablinks
  $(document).on("click", ".tablinks", function () {
    // Remove 'active' class from all tabs
    $(".tablinks").removeClass("active");

    // Add 'active' class to the clicked tab
    $(this).addClass("active");

    // Get the attempt number from the data-attempt attribute
    const attemptNumber = $(this).data("attempt");
    // Debugging to ensure event is triggered
    console.log("Tab clicked, Attempt Number: ", attemptNumber);
    // Call selectAttempt with the appropriate number
    selectAttempt(attemptNumber);
  });

  $(document).ready(function () {
    var cellMapping = {};
    // Call fetchCells to load data on page load
    // fetchInitialCells();

    // Enable sortable on both lists
    $("#path-list ul, #full-list ul")
      .sortable({
        connectWith: ".reorder, .reorder-full", // Allows cross-list dragging between path-list and full-list
        update: function () {
          updateDisplayPath("#path-list ul li", "cur_path");
          // update: function () {
          //   var order = [];
          //   var pathDescriptions = [];

          //   // Loop through the current path list and update the order and path descriptions
          //   $("#path-list ul li").each(function () {
          //     var cellId = $(this).attr("id").replace("cell-", ""); // Extract cell ID from the element's id
          //     order.push(cellId);
          //     var cellDescription = cellMapping[cellId];
          //     pathDescriptions.push(cellDescription);
          //   });

          //   // console.log("Order:", order);
          //   // console.log("Path Descriptions:", pathDescriptions);

          //   var arrowIcon = '<i class="bi bi-arrow-right"></i>';
          //   var pathHTML = "";

          //   // Option 1: Update the current path with the cell IDs
          //   // var pathByIDs = order.map((cellId) => {
          //   //   return `<span id="pathcell-${cellId}">${cellId}</span>`;
          //   // });
          //   // pathHTML = pathByIDs.join(` ${arrowIcon} `);

          //   // document.getElementById("cur_path").innerHTML = pathHTML;
          //   // Uncomment to enable Option 1

          //   // Option 2: Update the current path with the descriptions
          //   var pathByDescriptions = pathDescriptions.map((desc, index) => {
          //     return `<span id="pathcell-${order[index]}">${desc}</span>`;
          //   });
          //   pathHTML = pathByDescriptions.join(` ${arrowIcon} `);

          //   // Uncomment to enable Option 2
          //   document.getElementById("cur_path").innerHTML = pathHTML;

          // Calculates total time
          calculateTotalTimeCurrentPath();
        },
      })
      .disableSelection(); // Disable selection behavior to allow dragging
  });
});

/* Overview and main functionality */
function getUserInfo(afterReport = false) {
  thisAjax();

  function thisAjax() {
    $.ajax({
      type: "POST",
      url: "/req_userinfo",
      success: function (response) {
        // console.log("req_userinfo", response);
        if (response.result == "success") {
          if (response.pretest_done == true) {
            if (response.session_active == true) {
              loading(true);
              fetchQuestion();
              $("#attempt_point").text(
                "Attempt " + String(response.next_attempt)
              );
            } else {
              if (afterReport == false) {
                // Show page
                $("#non-session").removeClass("d-none");
                // Overview page
                $("#header_text").removeClass("d-none");
                $("#welcome_text").removeClass("d-none");
                $("#my_name").val(response.full_name);
                $("#username_text").text(response.full_name);
                $("#my_learner_id").val(response.user_id);
                $("#disclaimer_text").text(response.disclaimer);
                $("#attempt_disclaimer").text(
                  "Attempt " + String(response.next_attempt)
                );
                $("#attempt_point").text(
                  "Attempt " + String(response.next_attempt)
                );
                $("#attempt_point").addClass("d-none");

                if (response.photo_string != "") {
                  $("#profile_img").attr("src", response.photo_string);
                  $("#profile_img").attr("alt", "Embedded Image");
                } else {
                  $("#profile_img").attr(
                    "src",
                    "/static/images/profile_default.png"
                  );
                }

                // Highlight mastery
                $('td[useFor="mastery"]').each(function () {
                  this_cell_data =
                    response.mastery_list[parseInt($(this).attr("cellId")) - 1];
                  if (this_cell_data == true) {
                    $(this).removeClass("table-danger");
                    $(this).removeClass("table-success");
                    $(this).addClass("table-success");
                  } else {
                    $(this).removeClass("table-danger");
                    $(this).removeClass("table-success");
                    $(this).addClass("table-danger");
                  }
                });

                presentChart(
                  "learner_ability_chart",
                  "ability_chart_status",
                  response.learner_ability,
                  "",
                  [],
                  interpretPerformance,
                  "",
                  []
                );
                // console.log("req_userinfo__score_list", response.score_list);
                if (
                  response.score_list["Data Point"].length <
                  response.score_list["Timestamp"].length
                ) {
                  response.score_list["Timestamp"] = response.score_list[
                    "Timestamp"
                  ].slice(-response.score_list["Data Point"].length);
                }
                // console.log("req_userinfo__score_list", response.score_list);

                var map_data_array = [];
                for (i = 0; i < response.score_list["Data Point"].length; i++) {
                  map_data_array.push(
                    String(response.score_list.Extrainfo[0][i]) +
                      "/" +
                      String(response.score_list.Extrainfo[1][i])
                  );
                }
                // console.log("map_data_array", response);
                presentChart(
                  "learner_score_chart",
                  "ability_chart_status",
                  response.score_list,
                  "",
                  [],
                  null,
                  "",
                  map_data_array
                );

                // Make switchable
                // $("#view_switch_btn").on("click", function () {
                //   if (
                //     $("#view_switch_title").text().toLowerCase() ==
                //     "Performance history".toLowerCase()
                //   ) {
                //     $("#view_switch_title").text("Score History");
                //     $("#learner_score_chart").removeClass("d-none");
                //     $("#learner_ability_chart").addClass("d-none");
                //   } else {
                //     $("#view_switch_title").text("Performance History");
                //     $("#learner_ability_chart").removeClass("d-none");
                //     $("#learner_score_chart").addClass("d-none");
                //   }
                // });

                fetchReport();
                // Settings page
                if (response.settings[1].length > 0) {
                  // Unrandom
                  $("#random_check").prop("checked", false);
                  $("#random_box").addClass("d-none");
                  $("#select_box").removeClass("d-none");

                  // Only for start page
                  if (total_cell.length == 0) {
                    for (i = 0; i < response.settings[1].length; i++) {
                      addCell(true, response.settings[1][i]);
                    }
                  }
                } else {
                  $("#cell_num").val(response.settings[0]);
                }
              } else {
                $("#header_text").removeClass("d-none");
                // Highlight mastery
                $('td[useFor="mastery"]').each(function () {
                  this_cell_data =
                    response.mastery_list[parseInt($(this).attr("cellId")) - 1];
                  if (this_cell_data == true) {
                    $(this).removeClass("table-danger");
                    $(this).removeClass("table-success");
                    $(this).addClass("table-success");
                  } else {
                    $(this).removeClass("table-danger");
                    $(this).removeClass("table-success");
                    $(this).addClass("table-danger");
                  }
                });

                presentChart(
                  "learner_ability_chart",
                  "ability_chart_status",
                  response.learner_ability,
                  "",
                  [],
                  interpretPerformance,
                  "",
                  []
                );
                var map_data_array = [];
                for (i = 0; i < response.score_list["Data Point"].length; i++) {
                  map_data_array.push(
                    String(response.score_list.Extrainfo[0][i]) +
                      "/" +
                      String(response.score_list.Extrainfo[1][i])
                  );
                }
                presentChart(
                  "learner_score_chart",
                  "ability_chart_status",
                  response.score_list,
                  "",
                  [],
                  null,
                  "",
                  map_data_array
                );
              }
            }
          } else {
            window.location.pathname = "/pretest_start";
          }
        } else {
          alert(response.status);
        }
      },
    });
  }
}

// Initially load the user's path
function getUserPath() {
  thisAjax();

  function thisAjax() {
    $.ajax({
      type: "POST",
      url: "/req_get_user_path",
      success: function (response) {
        console.log("req_get_user_path", response);
        if (response.result == "success") {
          append_string = "";
          path = response.path;
          cpath = response.cpath;
          if (cpath.length == 0) {
            var cpath = path;
          }
          for (var i = 0; i < cpath.length; i++) {
            append_string +=
              "<li id=cell-" + cpath[i] + ">" + cpath[i] + "</li>";
          }
          $("#draggable_list").html(append_string);
          document.getElementById("cur_path").innerHTML = cpath;
          fetchCellTimes(response.path, response.cpath);
        }
      },
      error: function () {
        console.error("An error occurred while fetching the user's path.");
      },
    });
  }
}

function getTotalCellIndices() {
  thisAjax();

  function thisAjax() {
    $.ajax({
      type: "POST",
      url: "/req_get_total_cell",
      success: function (response) {
        if (response.result == "success") {
          for (i = 0; i < response.cell_list.length; i++) {
            cell_indices +=
              '<option value="' +
              response.cell_list[i][0] +
              '">Cell ' +
              response.cell_list[i][0] +
              ": " +
              response.cell_list[i][1] +
              "</option>";
          }
        }
      },
    });
  }
}
function fetchCellTimes(rpath, cpath) {
  // console.log("rpath:", rpath);
  // console.log("cpath:", cpath);

  var allCellIds = [];

  // Collect all cell IDs that are in the initial paths
  // $("#path-list ul li, #rec_path span").each(function () {
  // $("#path-list ul li").each(function () {
  //   var cellId = $(this).attr("id").replace("cell-", "");
  //   allCellIds.push(cellId);
  // });

  
}

function calculateTotalTimeCurrentPath() {
  var total_time = 0;

  // Loop through the current path and sum up the times from the cellTimes object
  $("#path-list ul li").each(function () {
    var cellId = $(this).attr("id").replace("cell-", "");
    if (cellTimes[cellId]) {
      total_time += cellTimes[cellId]; // Add the time for each cell
    }
  });

  var hours = Math.floor(total_time / 60);
  var minutes = total_time % 60;
  var timeText = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;

  // Display the total time in the est_time element
  $("#est_time").text(timeText);

  // Condition for exceeding time limits
  if (total_time < 150 || total_time > 210) {
    $("#est_time").removeClass("text-muted").css("color", "red");
    $("#time-note").show(); // Show the note if the time exceeds limits
  } else {
    $("#est_time").addClass("text-muted").css("color", "");
    $("#time-note").hide(); // Hide the note if the time is within limits
  }
}

// To generate time for system recommeneded path
function calculateTotalTimeRecommendedPath(rpath) {
  var total_time = 0;
  console.log("rpath", rpath);
  // Loop through the path array and sum up the times from the cellTimes object
  rpath.forEach(function (cellId) {
    if (cellTimes[cellId]) {
      total_time += cellTimes[cellId]; // Add the time for each cell
      // console.log("cellTimes[cellId]", cellTimes[cellId]);
      // console.log("total_time", total_time);
    }
  });
  var hours = Math.floor(total_time / 60);
  var minutes = total_time % 60;

  // Display the total time in hours and minutes in the est_time element
  var timeText = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
  $("#rec_est_time").text(timeText);
}

function getProfilePhoto() {
  thisAjax();

  function thisAjax() {
    $.ajax({
      type: "POST",
      url: "/req_get_profile_picture",
      success: function (response) {
        if (response.result == "success") {
          if (response.photo_string != "") {
            $("#profile_img").attr("src", response.photo_string);
            $("#profile_img").attr("alt", "Embedded Image");
          } else {
            $("#profile_img").attr("src", "/static/images/profile_default.png");
          }
        } else {
          alert(response.status);
        }
      },
    });
  }
}

// Fundamental function to display chart/graph
function presentChart(
  object_id,
  chart_status_id,
  dataset,
  title,
  label_name_array = [],
  bar_top_function = null,
  legend_name = "",
  map_data = []
) {
  var labels = [];
  var data_array = [];

  // Instantiate the chart
  var is_chart_existed = Chart.getChart($("#" + object_id));

  if (is_chart_existed) {
    is_chart_existed.destroy();
  }

  if (dataset.hasOwnProperty("Data Point") == true) {
    if (dataset["Data Point"].length > 0) {
      // Help reduce canvas drawing time and smoother transition
      for (let i = 0; i < dataset["Data Point"].length; i++) {
        if (
          label_name_array.length > 0 &&
          label_name_array.length == dataset["Data Point"].length
        ) {
          labels.push(label_name_array[i]);
        } else {
          labels.push(convertEpochToFormat(dataset.Timestamp[i]));
        }

        data_array.push(dataset["Data Point"][i]);
      }

      if (legend_name != "") {
        configure_legend_name = legend_name;
        legend_enable = true;
      } else {
        configure_legend_name = "Value";
        legend_enable = false;
      }

      if (bar_top_function == null && map_data.length == 0) {
        padding_top_val = 0;
      } else {
        padding_top_val = 40;
      }

      // Create an array of datasets
      const datasets = [
        {
          label: configure_legend_name,
          data: data_array,
          borderColor: "#e9953b",
          backgroundColor: "#e9953b",
          borderWidth: 1,
        },
      ];

      // Define the chart configuration options
      const chart_config = {
        type: "bar",
        data: {
          labels: labels,
          datasets: datasets,
        },
        options: {
          plugins: {
            title: {
              display: true,
              text: title,
              color: "Black",
              font: {
                weight: "bold",
                size: 20,
              },
            },
            datalabels: {
              anchor: "end",
              align: "end",
              color: "black",
              font: {
                size: 15,
              },
              rotation: -45,
              formatter: function (value, context) {
                if (bar_top_function != null) {
                  data = bar_top_function(value);
                } else {
                  // console.log(map_data.length);
                  if (map_data.length > 0) {
                    data = map_data[context.dataIndex];
                  } else {
                    data = "";
                  }
                }
                return data;
              },
            },
            legend: {
              display: legend_enable,
            },
          },
          scales: {
            y: {
              beginAtZero: true,
              max: 100,
              title: {
                display: true,
                text: "Percentage score", // Y-Axis Label
                color: "Black",
                font: {
                  size: 15,
                  weight: "bold",
                },
              },
            },
          },
          layout: {
            padding: {
              top: padding_top_val,
            },
          },
        },
      };
      $("#" + chart_status_id).html("");
      Chart.register(ChartDataLabels);
      const chart = new Chart($("#" + object_id), chart_config);
    } else {
      $("#" + chart_status_id).html(
        "<h4 class=\"text-center\">We couldn't find any assessment data for you at the moment. If you haven't taken the quiz yet, please start it to proceed.</h4>"
      );
    }
  } else {
    $("#" + chart_status_id).html(
      "<h4 class=\"text-center\">We couldn't find any assessment data for you at the moment. If you haven't taken the quiz yet, please start it to proceed.</h4>"
    );
  }
}

function interpretPerformance(ability_value) {
  var ceiling_value = parseInt(Math.ceil(ability_value));
  if (ceiling_value <= -2) {
    data = "Beginner";
  } else if (ceiling_value == -1) {
    data = "Novice";
  } else if (ceiling_value == 0) {
    data = "Competent";
  } else if (ceiling_value == 1) {
    data = "Skilled";
  } else if (ceiling_value == 2) {
    data = "Proficient";
  } else {
    data = "Expert";
  }

  return data;
}

/* Setting section */
function addCell(selected_cell = false, cell_no = 0) {
  latest_cell_box_id += 1;
  total_cell.push(latest_cell_box_id);
  var cell_choices = cell_indices;
  var allowedCells = [1, 2, 3, 4, 5, 18, 19, 20, 24, 25, 26, 27, 28, 29, 30]; // Only these cells should be selectable, for UAT
  var append_string;

  cell_choices = modifyCellChoices(cell_choices, allowedCells); // UAT fn to grey out non selectable cells

  append_string =
    '<div class="input-group mb-3" id="cell_form_' +
    latest_cell_box_id +
    '">' +
    '<label class="input-group-text" for="select_no"><i class="bi bi-paperclip"></i></label><select class="form-select" id="select_no_' +
    latest_cell_box_id +
    '" selectFor="cell_check">' +
    cell_choices +
    '</select><button class="btn btn-danger" onclick="removeCell(' +
    latest_cell_box_id +
    ')"><i class="bi bi-x-circle-fill"></i></button></div>';

  $("#cell_box").append(append_string);

  if (selected_cell == true) {
    $("#select_no_" + latest_cell_box_id).prop("selectedIndex", cell_no - 1);
  }
}

// // UAT function to grey out non selectable cells
function modifyCellChoices(cell_choices, allowedCells) {
  var parser = new DOMParser();
  var doc = parser.parseFromString(
    "<select>" + cell_choices + "</select>",
    "text/html"
  );
  var select = doc.querySelector("select");

  select.querySelectorAll("option").forEach(function (option) {
    if (!allowedCells.includes(parseInt(option.value))) {
      option.disabled = true;
      option.classList.add("text-muted", "bg-light");
    }
  });

  return select.innerHTML;
}

function removeCell(id) {
  $("#cell_form_" + id).remove();
  var index = total_cell.indexOf(id);
  if (index !== -1) {
    total_cell.splice(index, 1);
  }
}

function weightedRandom() {
  // Define the weights for each value
  // Higher weight means a higher chance of being selected
  const weights = [
    { value: 3, weight: 0.6 },
    { value: 4, weight: 0.3 },
    { value: 5, weight: 0.1 }
  ];

  // Calculate total weight
  const totalWeight = weights.reduce((total, item) => total + item.weight, 0);

  // Generate a random number between 0 and total weight
  const randomNum = Math.random() * totalWeight;

  // Select a value based on its weight
  let runningWeight = 0;
  for (let i = 0; i < weights.length; i++) {
    runningWeight += weights[i].weight;
    if (randomNum <= runningWeight) {
      return weights[i].value;
    }
  }
}

function saveSettings() {
  return new Promise((resolve, reject) => {
    var num_quiz = 0;
    var num_cell = 0;
    var num_timer = 0;
    var max_limit_quiz = 0;
    var random = $("#random_check").is(":checked");
    var cell_array = [];
    console.log("random", random);

    if (random == false) {
      $('select[selectFor="cell_check"]').each(function () {
        cell_array.push($(this).val());
      });

      cell_array = Array.from(new Set(cell_array)); // Remove duplication
      num_cell = cell_array.length;
    } else {
      num_cell = $("#cell_num").val();
    }
    console.log("num_cell", num_cell);

    // default
    num_quiz = 3;

    // num_quiz = weightedRandom();
    console.log("num_quiz", num_quiz);
    num_timer = 10000;
    // For Settings
    // num_quiz = $("#quiz_num").val();
    // num_timer = $("#timer_choice").val();
    max_limit_quiz = $("#max_limit").val();
    if (num_cell == 0) {
      saveSettingstatus = false;
      if (random) {
        $("#cell_num").addClass("is-invalid");
        alertCreation(
          "#main_alert_point",
          "danger",
          "At least number of cell must be 1"
        );
      } else {
        console.log("alert");
        alertCreation(
          "#main_alert_point",
          "danger",
          "At least 1 cell must be selected"
        );
      }
      resolve(false);
    } else {
      thisAjax(num_quiz, num_cell, cell_array, num_timer, max_limit_quiz)
        .then(() => {
          saveSettingstatus = true;
          resolve(true);
        })
        .catch(() => {
          saveSettingstatus = false;
          resolve(false);
        });
    }
  });
  function thisAjax(num_quiz, num_cell, check_quiz, num_timer, max_limit_quiz) {
    return new Promise((resolve, reject) => {
      $.ajax({
        type: "POST",
        url: "/req_save_settings",
        data: JSON.stringify({
          num_quiz: num_quiz,
          check_quiz: check_quiz,
          num_cell: num_cell,
          timer: num_timer,
          max_quiz: max_limit_quiz,
        }),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
          if (response.result == "success") {
            $("#cell_num").removeClass("is-invalid");
            // alertCreation(
            //   "#main_alert_point",
            //   "success",
            //   "Settings were saved.",
            //   true
            // );
            resolve();
          } else {
            alertCreation("#main_alert_point", "danger", response.status);
            reject();
          }
        },
        error: function () {
          reject();
        },
      });
    });
  }
}

// Original saveSettings function
// function saveSettings() {
//   var num_quiz = 0;
//   var num_cell = 0;
//   var num_timer = 0;
//   var max_limit_quiz = 0;
//   var random = $("#random_check").is(":checked");
//   var cell_array = [];

//   if (random == false) {
//     $('select[selectFor="cell_check"]').each(function () {
//       cell_array.push($(this).val());
//     });

//     cell_array = Array.from(new Set(cell_array)); // Remove duplication
//     num_cell = cell_array.length;
//   } else {
//     num_cell = $("#cell_num").val();
//   }

//   // default
//   num_quiz = 3;
//   num_timer = 1000;
//   // For Settings
//   // num_quiz = $("#quiz_num").val();
//   // num_timer = $("#timer_choice").val();
//   max_limit_quiz = $("#max_limit").val();
//   if (num_cell == 0) {
//     // saveSettingstatus = false;
//     if (random) {
//       $("#cell_num").addClass("is-invalid");
//       alertCreation(
//         "#main_alert_point",
//         "danger",
//         "At least number of cell must be 1"
//       );
//     } else {
//       console.log("alert");
//       alertCreation(
//         "#main_alert_point",
//         "danger",
//         "At least 1 cell must be selected"
//       );
//     }
//   } else {
//     thisAjax(num_quiz, num_cell, cell_array, num_timer, max_limit_quiz);
//     // saveSettingstatus = true;
//   }

//   function thisAjax(num_quiz, num_cell, check_quiz, num_timer, max_limit_quiz) {
//     $.ajax({
//       type: "POST",
//       url: "/req_save_settings",
//       data: JSON.stringify({
//         num_quiz: num_quiz,
//         check_quiz: check_quiz,
//         num_cell: num_cell,
//         timer: num_timer,
//         max_quiz: max_limit_quiz,
//       }),
//       contentType: "application/json; charset=utf-8",
//       dataType: "json",
//       success: function (response) {
//         if (response.result == "success") {
//           alertCreation(
//             "#main_alert_point",
//             "success",
//             "Settings were saved.",
//             true
//           );
//         } else {
//           alertCreation("#main_alert_point", "danger", response.status);
//         }
//       },
//     });
//   }
//   return saveSettingstatus;
// }

//fetchReportScore;
function fetchReport(switch_page = false) {
  thisAjax(switch_page);

  function thisAjax(switch_page) {
    $.ajax({
      type: "POST",
      // url: "/req_fetch_report",
      url: "/req_fetch_report_score",
      success: function (response) {
        if (response.result == "success") {
          $("#retake_quiz_btn").removeClass("disabled");
          console.log("retain_quiz_btn_enabled");
          console.log("response", response);
          //Placeholder LLM textbox
          // response.textboxdata = `Placeholder textbox. `; comment out 17/09/2024

          if (switch_page || response.n_attempt > 1) {
            seconds = response.total_second_used % 60;
            seconds = String(seconds);

            if (seconds < 10) {
              seconds = "0" + String(seconds);
            }

            minutes = String(Math.floor(response.total_second_used / 60));

            $("#report_time").val(
              String(minutes) + ":" + String(seconds) + " mins"
            );
            $("#report_correct").val(response.total_correct_ans);
            $("#report_num_quiz").val(response.total_quiz);

            sorted = response.cell_index.sort(function (a, b) {
              return a - b;
            });
            $("#selected_cell").val(sorted.join(", "));
            if (response.score_list["Data Point"].length <= 1) {
              data_label = ["Current"];
            } else {
              data_label = ["Previous", "Current"];
            }
            // To show ability level
            presentChart(
              "attempt_chart",
              "attempt_chart_status",
              response.score_list,
              "",
              data_label,
              interpretPerformance,
              "Ability Level"
            );

            var map_data_array = [];
            for (i = 0; i < response.score_list["Data Point"].length; i++) {
              map_data_array.push(
                String(response.score_list.Extrainfo[0][i]) +
                  "/" +
                  String(response.score_list.Extrainfo[1][i])
              );
            }
            // Converts to percentage to display
            let percentageDataPoints = [];

            for (let i = 0; i < response.score_list["Data Point"].length; i++) {
              let dataPoint = response.score_list["Extrainfo"][0][i];
              let extrainfo = response.score_list["Extrainfo"][1][i];
              if (extrainfo !== 0) {
                let percentage = (dataPoint / extrainfo) * 100;
                percentageDataPoints.push(Math.round(percentage));
              } else {
                percentageDataPoints.push(0); // To avoid division by zero
              }
            }

            response.score_list["Data Point"] = percentageDataPoints;
            // End of converting to percentage to display
            presentChart(
              "attempt_score_chart",
              "attempt_chart_status",
              response.score_list,
              "",
              [],
              null,
              "",
              map_data_array
            );
            createAttemptTab(response.n_attempt, "attempt_tab");
            createAnswerHistory(response.quiz_streak, "report_attempt_answer");
            $("#attempt_report").text("Attempt " + (response.n_attempt - 1));
            $("#attempt_report_ans").text(
              "Attempt " + String(selected_attempt_number)
            );
            $("#attempt_disclaimer").text(
              "Attempt " + String(response.n_attempt)
            );
            $("#attempt_point").text("Attempt " + String(response.n_attempt));
            $("#text_box_tbd").text(response.textboxdata);

            if (switch_page) {
              $("#quiz_page").addClass("d-none");
              $("#attempt_point").text("");
              $("#attempt_point").addClass("d-none");
              $("#abort_point").text("");
              clearInterval(timerInterval);
              timerInterval = false;
              timestamp_stop = 0;
              last_ts_server = 0;
              updateTimer(); // Use this to simultaneously get timer.
              $("#question_text").text("");
              $("#question_number").text("");
              $("#answer_text_1").text("");
              $("#answer_text_2").text("");
              $("#answer_text_3").text("");
              $("#answer_text_4").text("");
              $("#non-session").removeClass("d-none");
              $("#report").removeClass("d-none");
              loading();
              getUserInfo(true);
            } else {
              $("#report").removeClass("d-none");
            }

            $("#query_submit_btn").on("click", submitQuery);

            $("#retake_quiz_btn").on("click", function () {
              $("#tab-4").click();
            });

            $('button[useFor="reportonly"]').on("click", function () {
              $("#history_exp_card").removeClass("d-none");
              getExplanation($(this).attr("title"));
              document.getElementById("question_id").innerHTML =
                " " + $(this).attr("title");
            });
          } else {
            //$("#tab-pane-2").addClass("d-none");
            //$("#tab-2").addClass("disabled");
            $("#report").addClass("d-none");
            $("#retake_quiz_btn").off("click", function () {
              $("#tab-4").click();
            });
            $("#query_submit_btn").off("click", submitQuery);
          }
        } else {
          alert(response.status);
        }
      },
    });
  }
}

function submitQuery() {
  var query_msg = $("#query_msg").val();
  if (query_msg == "") {
    alertCreation("#query_alert_point", "danger", "No Query entered", true);
    return;
  }
  thisAjax(query_msg);

  function thisAjax(query) {
    $.ajax({
      type: "POST",
      url: "/req_submit_finish_query",
      data: JSON.stringify({ query: query }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function (response) {
        if (response.result == "success") {
          alertCreation("#query_alert_point", "info", response.status, true);
          $("#query_msg").val("");
        } else {
          alert(response.status);
        }
      },
    });
  }
}

function getExplanation(answer_id) {
  thisAjax(answer_id);
  function thisAjax() {
    $.ajax({
      type: "POST",
      url: "/req_get_explanation_history",
      data: JSON.stringify({
        answer_id: answer_id,
        attempt_num: selected_attempt_number,
      }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function (response) {
        if (response.result == "success") {
          // Populate the explanation details with the response data
          $("#history_question_text").text(response.question_text);
          $("#history_answer_text").text(response.answer_text);
          $("#history_explanation_text").text(response.explanation_text);
        } else {
          // Clear the content if the response is not successful
          $("#history_question_text").text("");
          $("#history_answer_text").text("");
          $("#history_explanation_text").text("");
          console.log(response.status);
        }
      },
      error: function (jqXHR, textStatus, errorThrown) {
        // Optional: Handle any errors from the AJAX request itself
        $("#history_question_text").text("");
        $("#history_answer_text").text("");
        $("#history_explanation_text").text("");
        console.error("AJAX request failed:", textStatus, errorThrown);
      }
    });
  }
}

function startQuiz() {
  loading(true);
  thisAjax();

  function thisAjax() {
    $.ajax({
      type: "POST",
      url: "/req_start_quiz",
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

/* Quiz section */
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

  // -- Timer --
  // timestamp_stop = timestamp_start + (m_duration * 60);
  // timerInterval = setInterval(dummyTimer, 1000);
  // last_ts_server = current_ts;
}

function dummyTimer(timestamp_start) {
  updateTimer(timestamp_start, true);

  // -- Timer --
  // Only set interval has this permission
  // function dummyTimer() {
  // updateTimer(true);
  // }
}

// function updateTimer(timeout=false) --> Timer
function updateTimer(timestamp_start, timeout = false) {
  var elapsed_seconds = last_ts_server - timestamp_start;
  // console.log(
  //   "Updating timer. Elapsed seconds:",
  //   elapsed_seconds,
  //   "Last timestamp server:",
  //   last_ts_server,
  //   "Timestamp start:",
  //   timestamp_start
  // );

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

  // -- Timer --
  // var remaining_seconds = timestamp_stop - last_ts_server;
  // var seconds = 0;
  // var minutes = 0;

  // seconds = remaining_seconds % 60;
  // seconds = String(seconds);

  // if (seconds < 10)
  // {
  //     seconds = "0" + String(seconds);
  // }

  // minutes = String(Math.floor(remaining_seconds / 60));

  // last_ts_server += 1;

  // $("#span_timer").text(minutes + ":" + seconds);

  // // Stop timer as time has passed for duration.
  // if (remaining_seconds <= 0)
  // {
  //     remaining_seconds = 0;
  //     clearInterval(timerInterval);
  //     timerInterval = false;
  //     $("#span_timer").text("0:00");
  //     if (timeout == true)
  //     {
  //         fetchQuestion(true);
  //     }

  // }
  // else
  // {
  //     $("#span_timer").text(minutes + ":" + seconds);
  // }
}

function abortAttempt() {
  loading(true);
  thisAjax();

  function thisAjax() {
    $.ajax({
      type: "POST",
      url: "/req_abort_attempt",
      success: function (response) {
        if (response.result == "success") {
          $("#quiz_page").addClass("d-none");
          $("#attempt_point").text("");
          $("#attempt_point").addClass("d-none");
          $("#abort_point").text("");
          $("#report").removeClass("d-none");
          clearInterval(timerInterval);
          timerInterval = false;
          timestamp_stop = 0;
          last_ts_server = 0;
          updateTimer(); // Use this to simultaneously get timer.
          $("#question_text").text("");
          $("#question_number").text("");
          $("#answer_text_1").text("");
          $("#answer_text_2").text("");
          $("#answer_text_3").text("");
          $("#answer_text_4").text("");
          $("#non-session").removeClass("d-none");
          $("#tab-1").click();
          getUserInfo(true);
          loading();
        } else {
          alert(response.status);
        }
      },
    });
  }
}

function abortButton() {
  var abort_btn_string =
    '<button class="btn btn-danger btn m-2 text-uppercase fw-bold" id="abort_btn">Abort this attempt <i class="bi bi-x-circle-fill"></i></button>';
  $("#abort_point").html(abort_btn_string);

  /* Quiz - Abort button */
  $("#abort_btn").on("click", function () {
    var abort_check = confirm(
      "Cancel the attempt? This will erase all current progress."
    );

    if (abort_check == true) {
      abortAttempt();
    }
  });
}

function fetchQuestion(fetch_time_out = false) {
  loading(true);
  $("#check_").prop("checked", false);
  $('input[checkbox-role="choice_selector"]').each(function () {
    $(this).prop("checked", false);
  });

  $("#report").addClass("d-none");
  $("#non-session").addClass("d-none");
  $("#header_text").removeClass("d-none");
  $("#welcome_text").addClass("d-none");
  $("#adt_text").removeClass("d-none");
  $("#attempt_point").removeClass("d-none");
  thisAjax(fetch_time_out);
  abortButton();

  function thisAjax(fetch_time_out) {
    $.ajax({
      type: "POST",
      url: "/req_fetch_question",
      data: JSON.stringify({ timeout: fetch_time_out }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function (response) {
        // Todo: randomise AQ order

        if (response.result == "success") {
          if (response.question == "") {
            if (response.reason == "no_quiz") {
              alertCreation(
                "#quiz_alert_point",
                "success",
                "You are already gotten all knowledges, aborting attempt.",
                true
              );
              loading(true);
              fetchReport(true);
            } else if (response.reason == "complete") {
              alertCreation(
                "#quiz_alert_point",
                "info",
                "Quiz completed, showing result.",
                true
              );
              loading(true);
              fetchReport(true);
            } else if (response.reason == "timeout") {
              alertCreation(
                "#quiz_alert_point",
                "info",
                "Timer is expired, showing result.",
                true
              );
              loading(true);
              fetchReport(true);
            } else {
              alertCreation(
                "#quiz_alert_point",
                "danger",
                "Error - No question data found, please contact admin",
                true
              );
            }
          } else {
            $("#quiz_page").removeClass("d-none");
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
            $("#show_exp_btn").addClass("disabled");
            $("#explanation_card").addClass("fade");
            $("#explanation_text").text("");
            $("#submit_btn").removeClass("disabled");
            $("#idk_btn").removeClass("disabled");
            $("#submit_btn").removeClass("d-none");
            $("#idk_btn").removeClass("d-none");
            $("#next_question").off("click", dummyBind);
            $("#next_question").addClass("d-none");
            $("#next_question").addClass("disabled");
            createAttemptTab(response.n_attempt, "attempt_tab");
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

function dummyBind() {
  fetchQuestion();
}

function submitAnswer(answer_choice) {
  loading(true);
  thisAjax(answer_choice);
  console.log("answer_choice:", answer_choice);
  function thisAjax(answer_choice) {
    $.ajax({
      type: "POST",
      url: "/req_submit_answer",
      data: JSON.stringify({ selected_choice: answer_choice }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function (response) {
        loading();
        console.log("response", response);
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
                $(this).text("-");
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
          $("#next_question").on("click", dummyBind);
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

function updatePath() {
  thisAjax();
  function thisAjax() {
    cur_path_ids = [];
    // Get id from draggable list since the display field doesn't contain id
    $("#path-list ul li").each(function () {
      var cellId = $(this).attr("id").replace("cell-", ""); // Extract cell ID from the element's id
      cur_path_ids.push(cellId);
    });
    cur_path_ids = cur_path_ids.filter((i) => i.trim() != "").join(",");
    console.log("upating cur_path: ", cur_path_ids);
    // Send the cleaned IDs to the backend
    $.ajax({
      method: "POST",
      url: "/update_path",
      data: "path=" + cur_path_ids,
      cache: false,
    });
  }
}
function fetchCells() {
  $.ajax({
    type: "POST",
    url: "/req_get_total_cell",
    success: function (response) {
      if (response.result === "success") {
        // Clear the current list
        $("#full-list ul").empty();
        // Loop through the cell list and append each cell to the full-list
        $.each(response.cell_list, function (index, cell) {
          // Assuming each cell is an array with [cell_id, cell_description]
          /*$("#full-list ul").append(
            '<li id="' + cell[0] + '">' + cell[0] + ": " + cell[1] + "</li>"
          );*/
          console.log("cell: ", cell);
          full_list = document.getElementById("unassigned-list");
          entry = document.createElement("li");
          text = document.createTextNode(
            cell[0] + ": " + cell[1] + " (" + cell[3] + " mins)"
          );
          entry.appendChild(text);
          entry.id = cell[0];
          entry.title = cell[2];
          full_list.appendChild(entry);
        });
      } else {
        console.error("Failed to fetch cell data: " + response.status);
      }
    },
    error: function () {
      console.error("An error occurred while fetching cell data.");
    },
  });
}

function fetchInitialCells() {
  $.ajax({
    type: "POST",
    url: "/req_get_total_cell",
    success: function (response) {
      if (response.result === "success") {
        // Clear the current list on new load
        $("#full-list ul").empty();
        cellMapping = {};
        cellFullMapping = {};
        cellTimingsMapping = {};

        // Get the IDs already in the current path
        var currentPathIds = [];
        $("#path-list ul li").each(function () {
          var cellId = $(this).attr("id").replace("cell-", "");
          currentPathIds.push(cellId);
        });

        // Loop through the cell list and append each cell to the full-list if not in current path
        $.each(response.cell_list, function (index, cell) {
          var cellId = String(cell[0]); // Convert cellId to string, else comparison fails
          var cellDescription = cell[1];
          var cellFullDescription = cell[2];
          var cellTimings = cell[3];
          cellMapping[cellId] = cellDescription;
          cellFullMapping[cellId] = cellFullDescription;
          cellTimingsMapping[cellId] = cellTimings;

          // Only add cells to full-list if they are not in the current path
          if (!currentPathIds.includes(cellId)) {
            /*$("#full-list ul").append(
              '<li id="cell-' +
                cellId +
                '">' +
                cellId +
                ": " +
                cellDescription +
                "</li>"
            );*/
            full_list = document.getElementById("unassigned-list");
            entry = document.createElement("li");
            entry.id = "cell-" + cellId;
            text = document.createTextNode(
              cellId + ": " + cellDescription + " (" + cellTimings + " mins)"
            );
            entry.appendChild(text);
            entry.title = cellFullDescription;
            full_list.appendChild(entry);
          }
        });

        // Update the path-list with descriptions
        updatePathList(cellMapping, cellFullMapping, cellTimingsMapping);
        /* Display recommended path
        rec_path_ids = document
          .getElementById("rec_path")
          .innerHTML.split(",");
        var pathDescriptions = [];
        for (var i = 0; i < rec_path_ids.length; i++) {
          var cellId = rec_path_ids[i];
          var cellDescription = cellMapping[cellId];
          pathDescriptions.push(cellDescription);
        }
        var arrowIcon = '<i class="bi bi-arrow-right"></i>';
        document.getElementById("rec_path").innerHTML =
          pathDescriptions.join(" " + arrowIcon + " ");*/
        // Display current path
        updateDisplayPath("#path-list ul li", "cur_path");
      } else {
        console.error("Failed to fetch cell data: " + response.status);
      }
    },
    error: function () {
      console.error("An error occurred while fetching cell data.");
    },
  });
}

// Function to update the path list with descriptions based on the initial path
function updatePathList(cellMapping, cellFullMapping, cellTimingsMapping) {
  // Loop through the current path list and replace numerical IDs with descriptions
  $("#path-list ul li").each(function () {
    var cellId = $(this).attr("id").replace("cell-", "");
    var cellDescription = cellMapping[cellId]; // Use the mapping to get the description
    if (cellDescription) {
      $(this).text(
        cellId +
          ": " +
          cellDescription +
          " (" +
          cellTimingsMapping[cellId] +
          " mins)"
      );
      $(this).attr("title", cellFullMapping[cellId]);
    }
  });
}
// Function to update the display of path description under recommended path and current path section
function updateDisplayPath(list_field, display_field) {
  var pathDescriptions = [];
  // Loop through the path list and update the order and path descriptions
  $(list_field).each(function () {
    var cellId = $(this).attr("id").replace("cell-", ""); // Extract cell ID from the element's id
    // console.log("cellId: ", cellId);
    pathDescriptions.push(cellMapping[cellId]); // Use the mapping to get the description
  });
  var arrowIcon = '<i class="bi bi-arrow-right"></i>';
  document.getElementById(display_field).innerHTML = pathDescriptions.join(
    " " + arrowIcon + " "
  );
}

function getQuizStreak(attempt_num) {
  thisAjax(attempt_num);
  function thisAjax() {
    $.ajax({
      type: "POST",
      url: "/req_get_quiz_streak",
      data: JSON.stringify({ attempt_num: selected_attempt_number }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function (response) {
        if (response.result == "success") {
          createAnswerHistory(response.quiz_streak, "report_attempt_answer");
          $('button[useFor="reportonly"]').on("click", function () {
            $("#history_exp_card").removeClass("d-none");
            getExplanation($(this).attr("title"));
            document.getElementById("question_id").innerHTML =
              " " + $(this).attr("title");
          });
        } else {
          console.log("response.status", response.status);
        }
      },
    });
  }
}

// Before QE2
// function selectAttempt(attempt_num) {
//   selected_attempt_number = attempt_num;
//   // Display 'Baseline' for attempt 1, otherwise show 'Attempt X'
//   if (attempt_num === 1) {
//     document.getElementById("attempt_report_ans").innerHTML = "Baseline Quiz";
//   } else {
//     document.getElementById("attempt_report_ans").innerHTML =
//       "Attempt " + (attempt_num - 1).toString();
//   }
//   getQuizStreak(selected_attempt_number);
//   getExplanation(1);
//   document.getElementById("question_id").innerHTML = " 1";
// }

// function createAttemptTab(tab_num, append_place) {
//   let append_string = "";
//   for (let i = 0; i < tab_num - 1; i++) {
//     let attempt_num = i + 1;
//     if (attempt_num === 1) {
//       // Display 'Baseline' for the first attempt
//       append_string +=
//         '<button class="tablinks" data-attempt="' +
//         attempt_num +
//         '">Baseline</button>';
//     } else {
//       // Display 'Attempt 1', 'Attempt 2', and so on for subsequent attempts
//       append_string +=
//         '<button class="tablinks" data-attempt="' +
//         attempt_num +
//         '">Attempt ' +
//         (attempt_num - 1).toString() +
//         "</button>";
//     }
//   }

function selectAttempt(attempt_num) {
  selected_attempt_number = attempt_num;
  // Display 'Baseline' for attempt 1, otherwise show 'Attempt X'
  if (attempt_num === 1) {
    document.getElementById("attempt_report_ans").innerHTML = "Baseline Quiz";
  } else {
    document.getElementById("attempt_report_ans").innerHTML =
      "Attempt " + (attempt_num-1).toString();
  }
  getQuizStreak(selected_attempt_number);
  getExplanation(1);
  document.getElementById("question_id").innerHTML = " 1";
}

function createAttemptTab(tab_num, append_place) {
  let append_string = "";
  // Start the loop from the second attempt (index 1)
  for (let i = 1; i < tab_num; i++) {
    let attempt_num = i + 1; // The attempt number starts from 2 in this case
    // Add 'active' class to the first tab created to make it active by default
    let activeClass = i === 1 ? " active" : "";
    // Display 'Attempt 2', 'Attempt 3', and so on for subsequent attempts
    append_string +=
      '<button class="tablinks' + activeClass + '" data-attempt="' +
      attempt_num +
      '">Attempt ' +
      (attempt_num - 1).toString() +
      "</button>";
  }

  // Set the HTML content of the target element
  $("#" + append_place).html(append_string);

  // Trigger the click event for the first tab to select it by default
  $(".tablinks.active").trigger("click");
}

//         if (i < array.length)
//         {
//             if (array[i] == 1) // Success
//             {
//                 append_string += "<div class=\"col bg-success border\" useFor=\"reportonly\" style=\"color:white\">"
//                 append_string += String(i+1) + "</div>"
//             }
//             else if (array[i] == -1)
//             {
//                 append_string += "<div class=\"col bg-secondary border\" useFor=\"reportonly\" style=\"color:white\">"
//                 append_string += String(i+1) + "</div>"
//             }
//             else
//             {
//                 append_string += "<div class=\"col bg-danger border\" useFor=\"reportonly\" style=\"color:white\">"
//                 append_string += String(i+1) + "</div>"
//             }
//         }
//         else
//         {
//             append_string += "<div class=\"col\">&nbsp;</div>"
//         }

//         if (((i % 10) == 9)) // 10, 20, 30, 40, ...
//         {
//             if (row_started == true)
//             {
//                 append_string += "</div>"
//                 row_started = false;
//             }
//         }
//     }

//     $("#" + append_place).html(append_string);
// }