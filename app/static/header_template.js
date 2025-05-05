/* Event assignment to object */
$(document).ready(function () {
  loadLogo();
  responsiveTable();
  loginADQ();
  // comment out for automatically logging in
  // $("#login_btn").click(function (event) {
  //   event.preventDefault();
  //   loginADQ();
  // });

  $("#reset_pw_btn").click(function () {
    switchPage();
  });

  $("#login-form").submit(function (event) {
    event.preventDefault(); // Prevent form default html-server submission, fully using javascript
  });

  $(window).resize(function () {
    // Call resizeTable function when window is resized
    responsiveTable();
  });
  // Toggle password visibility
  $("#togglePassword").click(function () {
    const password = $("#login_user_pw");
    const type = password.attr("type") === "password" ? "text" : "password";
    password.attr("type", type);

    // Toggle the eye / eye-slash icon
    $(this).find("i").toggleClass("bi-eye bi-eye-slash");
  });
});

function loadLogo() {
  var element_existed = $("#login-form").length;

  image_path = "/static/images/cpfm.png";
  if (element_existed) {
    $.ajax({
      url: image_path,
      type: "HEAD",
      success: function () {
        $("#logo_place").html('<img height="100" src="' + image_path + '">');
      },
      error: function () {
        $("#logo_place").text("");
      },
    });
  }
}

/* These are event assignments, they will not be executed once document (HTML) is ready */
/* Function library */
function loginADQ(state) {
  thisAjax();

  function thisAjax() {
    var this_username = $("#login_user_id").val();
    var this_password = $("#login_user_pw").val();
    this_password = btoa(this_password);
    var remember_me = $("#rememberme").is(":checked");
    
    $.ajax({
      type: "POST",
      url: "/access/" + launchId +"/",
      data: JSON.stringify({
        username: this_username,
        password: this_password,
        remember: remember_me,
      }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function (response) {
        if (response.result == "success") {
          alertCreation(
            "#login_alert_point",
            "success",
            "Login successfully, reloading...",
            true
          );
          // If you need to use the session data before redirecting
          var sessionData = response.session;
          console.log("Session Data: ", response.posttest_start);
          location.reload();
        } else {
          alertCreation("#login_alert_point", "danger", response.status);
        }
      },
    });
  }
}

function responsiveTable() {
  var user_width = screen.width;
  // Function to resize the table based on window width
  var windowWidth = $(window).width();

  width_cal = (windowWidth / user_width) * 100;
  upper_range = 60;
  lower_range = 20;

  if (width_cal >= upper_range) {
    $("#responsive_table").css("width", String(lower_range) + "%");
  } else if (width_cal < upper_range && width_cal > lower_range) {
    new_width =
      ((upper_range - width_cal) / (upper_range - lower_range)) *
        (upper_range - lower_range) +
      lower_range;

    new_width = parseInt(Math.floor(new_width));
    $("#responsive_table").css("width", String(new_width) + "%");
  } else {
    $("#responsive_table").css("width", String(upper_range) + "%");
  }
}

function switchPage() {
  if ($("#normal_form").hasClass("d-none")) {
    // Show normal
    $("#normal_form").removeClass("d-none");
    $("#forgot_form").addClass("d-none");
    $("#submit_pw_btn").addClass("disabled");
    $("#submit_pw_btn").off("click", submitPassword);
    $("#back_login_btn").off("click", switchPage);
  } else {
    $("#normal_form").addClass("d-none");
    $("#forgot_form").removeClass("d-none");
    $("#submit_pw_btn").removeClass("disabled");
    $("#submit_pw_btn").on("click", submitPassword);
    $("#back_login_btn").on("click", switchPage);
  }
}

function submitPassword() {
  error = 0;
  $('input[reset_type="credential"]').each(function () {
    if ($(this).val() == "") {
      $(this).addClass("is-invalid");
      error = 1;
    } else {
      $(this).removeClass("is-invalid");
    }
  });

  if (error == 1) {
    alertCreation(
      "#reset_alert_point",
      "danger",
      "Information can not be emptied"
    );
  } else {
    if ($("#reset_user_pw_1").val() != $("#reset_user_pw_2").val()) {
      alertCreation(
        "#reset_alert_point",
        "danger",
        "Password and Confirm password are not matched"
      );
    } else {
      var username = $("#reset_user_id").val();
      var name_user = $("#reset_user_name").val();
      var password = $("#reset_user_pw_1").val();
      password = btoa(password);
      thisAjax(username, name_user, password);
    }
  }

  function thisAjax(user, name, password) {
    $.ajax({
      url: "/req_reset_password",
      type: "POST",
      data: JSON.stringify({
        username: user,
        name: name,
        password: password,
      }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function (response) {
        if (response.result == "success") {
          alertCreation("#reset_alert_point", "success", response.status, true);
        } else {
          alertCreation("#reset_alert_point", "danger", response.status);
        }
      },
    });
  }
}

//Todo: Alert window, to change to Toast
function alertCreation(alert_point, bootstrap_color, message, fadable = false) {
  onclick_function = "$('" + alert_point + "').text();";
  // Spinner
  var spinner = '<div id="alert_spinner" class="spinner-border spinner-border-sm text-light me-2" role="status"></div>';

  var append_text =
    '<div class="alert alert-' +
    bootstrap_color +
    ' alert-dismissible fade show" role="alert">' + spinner;
  append_text += "<strong>" + message + "</strong>";
  append_text +=
    '<button closeFor="' +
    alert_point +
    '" type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>';

  $(alert_point).html(append_text);

  if (fadable) {
    alertFade(alert_point);
  }
}

function alertCreationTemp(alert_point, bootstrap_color, message, fadable = false) {
  onclick_function = "$('" + alert_point + "').text();";
  // Spinner
  var spinner = '<div id="alert_spinner" class="spinner-border spinner-border-sm text-light me-2" role="status"></div>';

  var append_text =
    '<div class="alert alert-' +
    bootstrap_color +
    ' alert-dismissible fade show" role="alert">' + spinner;
  append_text += "<strong>" + message + "</strong>";
  append_text +=
    '<button closeFor="' +
    alert_point +
    '" type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>';

  $(alert_point).html(append_text);

  if (fadable) {
    alertFadeTemp(alert_point);
  }
}

function alertFade(alert_point) {
  setTimeout(function () {
    // Remove the spinner element after 10 seconds
    $('#alert_spinner').remove();
    $('button[closeFor="' + alert_point + '"]').click();
  }, 5); // 10 seconds fade
}

function alertFadeTemp(alert_point) {
  setTimeout(function () {
    // Remove the spinner element after 20 seconds
    $('#alert_spinner').remove();
    $('button[closeFor="' + alert_point + '"]').click();
    loading(true)
  }, 5000); // 20 seconds fade
}

function loading(state = false) {
  if (state) {
    $("#loading").modal("show");
  } else {
    $("#loading").modal("hide");
  }
}

function upload(file_input_id, endpoint) {
  var file_upload = new FileReader();
  file_upload.onload = function (e) {
    file_base64 = e.target.result;
    thisAjax(file_base64, endpoint);
  };

  file_upload.readAsDataURL(document.getElementById(file_input_id).files[0]);

  function thisAjax(filestring, endpoint) {
    $.ajax({
      url: endpoint,
      type: "POST",
      data: JSON.stringify({
        file_content_string: filestring,
      }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function (response) {
        if (response.result == "success") {
          alertCreation("#main_alert_point", "success", response.message, true);
        } else {
          alertCreation("#main_alert_point", "danger", response.message);
        }
      },
    });
  }
}

function download(endpoint) {
  thisAjax(endpoint);
  function thisAjax(endpoint) {
    $.ajax({
      type: "POST",
      url: endpoint,
      dataType: "json",
      success: function (response) {
        if (response.result == "success") {
          var blob = convertToBlob(
            response.json_string,
            "application/octet-stream"
          );
          makeDownload(blob, response.filename);
        } else {
          alertCreation(
            "nonsession_alert_point",
            "danger",
            "Unable to download requested file"
          );
        }
      },
    });
  }

  function convertToBlob(json_string, mimeType) {
    var byteCharacters = atob(json_string);
    var byteNumbers = new Array(byteCharacters.length);
    for (var i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }

    var byteArray = new Uint8Array(byteNumbers);
    var blob = new Blob([byteArray], { type: mimeType });

    return blob;
  }

  function makeDownload(blob, filename) {
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.style.display = "none";
    a.href = url;
    a.download = filename; // Set the desired downloaded filename
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }
}

function convertEpochToFormat(epochTime) {
  var date = new Date(epochTime * 1000); // Convert epoch time to milliseconds

  var year = date.getFullYear();
  var month = String(date.getMonth() + 1).padStart(2, "0");
  var day = String(date.getDate()).padStart(2, "0");
  var hour = String(date.getHours()).padStart(2, "0");
  var minute = String(date.getMinutes()).padStart(2, "0");
  var second = String(date.getSeconds()).padStart(2, "0");

  var formattedDate =
    day + "-" + month + "-" + year + " " + hour + ":" + minute + ":" + second;
  return formattedDate;
}
