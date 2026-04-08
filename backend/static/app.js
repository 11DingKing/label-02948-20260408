/**
 * BPMN to Image Converter - Frontend Logic
 */
(function () {
  "use strict";

  // DOM elements
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const fileInfo = document.getElementById("fileInfo");
  const fileName = document.getElementById("fileName");
  const fileSize = document.getElementById("fileSize");
  const removeFile = document.getElementById("removeFile");
  const formatSelect = document.getElementById("formatSelect");
  const dpiGroup = document.getElementById("dpiGroup");
  const scaleGroup = document.getElementById("scaleGroup");
  const dpiInput = document.getElementById("dpiInput");
  const scaleInput = document.getElementById("scaleInput");
  const convertBtn = document.getElementById("convertBtn");
  const previewBtn = document.getElementById("previewBtn");
  const previewCard = document.getElementById("previewCard");
  const previewImage = document.getElementById("previewImage");
  const previewMeta = document.getElementById("previewMeta");
  const downloadBtn = document.getElementById("downloadBtn");
  const toastContainer = document.getElementById("toastContainer");

  let selectedFile = null;
  let lastImageData = null;

  // ===== Toast =====
  function showToast(message, type) {
    type = type || "success";
    var toast = document.createElement("div");
    toast.className = "toast toast-" + type;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    setTimeout(function () {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 3000);
  }

  // ===== File handling =====
  function formatBytes(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
  }

  function setFile(file) {
    if (!file) return;
    var ext = file.name.split(".").pop().toLowerCase();
    if (ext !== "bpmn" && ext !== "xml") {
      showToast("请选择 .bpmn 或 .xml 文件", "error");
      return;
    }
    if (file.size > 16 * 1024 * 1024) {
      showToast("文件大小不能超过 16MB", "error");
      return;
    }
    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = formatBytes(file.size);
    fileInfo.style.display = "flex";
    dropzone.style.display = "none";
    convertBtn.disabled = false;
    previewBtn.disabled = false;
  }

  function clearFile() {
    selectedFile = null;
    fileInput.value = "";
    fileInfo.style.display = "none";
    dropzone.style.display = "block";
    convertBtn.disabled = true;
    previewBtn.disabled = true;
    previewCard.style.display = "none";
    lastImageData = null;
  }

  // ===== Drag & Drop =====
  dropzone.addEventListener("click", function () {
    fileInput.click();
  });

  fileInput.addEventListener("change", function () {
    if (fileInput.files.length > 0) setFile(fileInput.files[0]);
  });

  dropzone.addEventListener("dragover", function (e) {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", function () {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", function (e) {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) setFile(e.dataTransfer.files[0]);
  });

  removeFile.addEventListener("click", clearFile);

  // ===== Format toggle =====
  formatSelect.addEventListener("change", function () {
    var isPng = formatSelect.value === "png";
    dpiGroup.style.display = isPng ? "block" : "none";
    scaleGroup.style.display = isPng ? "block" : "none";
  });

  // ===== Loading state =====
  function setLoading(btn, loading) {
    var textEl = btn.querySelector(".btn-text");
    var loadingEl = btn.querySelector(".btn-loading");
    if (textEl) textEl.style.display = loading ? "none" : "inline";
    if (loadingEl) loadingEl.style.display = loading ? "inline-flex" : "none";
    btn.disabled = loading;
  }

  // ===== Convert (download) =====
  convertBtn.addEventListener("click", function () {
    if (!selectedFile) return;
    setLoading(convertBtn, true);

    var formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("format", formatSelect.value);
    formData.append("dpi", dpiInput.value);
    formData.append("scale", scaleInput.value);

    fetch("/api/convert", { method: "POST", body: formData })
      .then(function (res) {
        if (!res.ok) {
          return res.json().then(function (data) {
            throw new Error(data.error || "转换失败");
          });
        }
        return res.blob();
      })
      .then(function (blob) {
        var url = URL.createObjectURL(blob);
        var a = document.createElement("a");
        var ext = formatSelect.value === "svg" ? "svg" : "png";
        a.href = url;
        a.download = selectedFile.name.replace(/\.[^.]+$/, "") + "." + ext;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast("转换成功，文件已下载", "success");
      })
      .catch(function (err) {
        showToast(err.message, "error");
      })
      .finally(function () {
        setLoading(convertBtn, false);
      });
  });

  // ===== Preview =====
  previewBtn.addEventListener("click", function () {
    if (!selectedFile) return;
    previewBtn.disabled = true;
    previewBtn.textContent = "加载中...";

    var formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("format", formatSelect.value);
    formData.append("dpi", dpiInput.value);
    formData.append("scale", scaleInput.value);

    fetch("/api/convert/preview", { method: "POST", body: formData })
      .then(function (res) {
        if (!res.ok) {
          return res.json().then(function (data) {
            throw new Error(data.error || "预览失败");
          });
        }
        return res.json();
      })
      .then(function (data) {
        lastImageData = data;
        previewImage.src = data.image;
        previewMeta.textContent =
          "格式: " + data.format.toUpperCase() + " | 大小: " + formatBytes(data.size);
        previewCard.style.display = "block";
        previewCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
        showToast("预览生成成功", "success");
      })
      .catch(function (err) {
        showToast(err.message, "error");
      })
      .finally(function () {
        previewBtn.disabled = false;
        previewBtn.textContent = "预览";
      });
  });

  // ===== Download from preview =====
  downloadBtn.addEventListener("click", function () {
    if (!lastImageData) return;
    var a = document.createElement("a");
    a.href = lastImageData.image;
    var ext = lastImageData.format === "svg" ? "svg" : "png";
    a.download = (selectedFile ? selectedFile.name.replace(/\.[^.]+$/, "") : "diagram") + "." + ext;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    showToast("图片已下载", "success");
  });
})();
