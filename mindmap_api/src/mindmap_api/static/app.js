(function () {
  "use strict";

  var reqcons = document.getElementById("reqcons");
  var reqconsCount = document.getElementById("reqcons-count");
  var btnRun = document.getElementById("btn-run");
  var spinner = document.getElementById("spinner");
  var errorBox = document.getElementById("error-box");
  var resultSection = document.getElementById("result-section");
  var resultMd = document.getElementById("result-md");
  var btnCopy = document.getElementById("btn-copy");
  var btnDownload = document.getElementById("btn-download");

  // --- Character count ---
  reqcons.addEventListener("input", function () {
    var len = reqcons.value.length;
    reqconsCount.textContent = len;
    reqconsCount.parentElement.classList.toggle("over", len > 1000);
  });

  // --- Run ---
  btnRun.addEventListener("click", function () {
    var apiKey = document.getElementById("api-key").value.trim();
    var text = reqcons.value.trim();
    var qchar = document.getElementById("qchar").value.trim();
    var ppc = document.getElementById("ppc").value.trim();

    // Validation
    if (!apiKey) {
      showError("API Key を入力してください。");
      return;
    }
    if (!text) {
      showError("要件文を入力してください。");
      return;
    }
    if (text.length > 1000) {
      showError("要件文は1000文字以内にしてください。");
      return;
    }

    hideError();
    resultSection.style.display = "none";
    btnRun.disabled = true;
    spinner.style.display = "inline";

    var body = { reqcons: text };
    if (qchar) body.qchar = qchar;
    if (ppc) body.ppc = ppc;

    fetch("/v1/mindmap/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey,
      },
      body: JSON.stringify(body),
    })
      .then(function (resp) {
        if (!resp.ok) {
          return resp.json().then(
            function (data) {
              throw { status: resp.status, detail: data.detail || "Unknown error" };
            },
            function () {
              throw { status: resp.status, detail: resp.statusText };
            }
          );
        }
        return resp.json();
      })
      .then(function (data) {
        resultMd.textContent = data.mindmap_markdown;
        resultSection.style.display = "block";
      })
      .catch(function (err) {
        if (err.status) {
          var msg = err.status + " — ";
          if (err.status === 401) msg += "API Key が正しくありません。";
          else if (err.status === 422) msg += "入力内容に問題があります: " + err.detail;
          else if (err.status === 500) msg += "サーバーエラー: " + err.detail;
          else msg += err.detail;
          showError(msg);
        } else {
          showError("通信エラー: " + (err.message || err));
        }
      })
      .finally(function () {
        btnRun.disabled = false;
        spinner.style.display = "none";
      });
  });

  // --- Copy ---
  btnCopy.addEventListener("click", function () {
    var text = resultMd.textContent;
    if (!text) return;
    navigator.clipboard.writeText(text).then(function () {
      var orig = btnCopy.textContent;
      btnCopy.textContent = "コピーしました";
      setTimeout(function () { btnCopy.textContent = orig; }, 1500);
    });
  });

  // --- Download ---
  btnDownload.addEventListener("click", function () {
    var text = resultMd.textContent;
    if (!text) return;
    var blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "mindmap.md";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  // --- Helpers ---
  function showError(msg) {
    errorBox.textContent = msg;
    errorBox.style.display = "block";
  }
  function hideError() {
    errorBox.style.display = "none";
  }
})();
