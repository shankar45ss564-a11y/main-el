// health-records.js - Health Records Management

let currentRecord = null;
let allHealthRecords = [];

// Initialize page
document.addEventListener("DOMContentLoaded", function () {
  // Set default date to today
  const today = new Date().toISOString().split("T")[0];
  document.getElementById("recordDate").value = today;

  // Load health records
  loadHealthRecords();

  // Event listeners
  document
    .getElementById("createHealthRecordForm")
    .addEventListener("submit", handleCreateHealthRecord);
  document
    .getElementById("searchPatientLink")
    .addEventListener("click", (e) => {
      e.preventDefault();
      const modal = new bootstrap.Modal(
        document.getElementById("patientSearchModal"),
      );
      modal.show();
    });
  document
    .getElementById("searchPatientBtn")
    .addEventListener("click", handleSearchPatient);
  document
    .getElementById("applyFiltersBtn")
    .addEventListener("click", applyFilters);
  document
    .getElementById("clearFiltersBtn")
    .addEventListener("click", clearFilters);

  // OCR scan & fill
  const scanBtn = document.getElementById("scanFillBtn");
  if (scanBtn) {
    scanBtn.addEventListener("click", handleScanAndFill);
  }

  // Check for URL params
  const urlParams = new URLSearchParams(window.location.search);
  const patientId = urlParams.get("patient_id");
  const visitId = urlParams.get("visit_id");
  const contextId = urlParams.get("context_id");

  if (patientId) {
    document.getElementById("patientId").value = patientId;
    document.getElementById("filterPatientId").value = patientId;
  }
  if (visitId) {
    document.getElementById("visitId").value = visitId;
  }
  if (contextId) {
    document.getElementById("contextId").value = contextId;
  }
});

// Load all health records
async function loadHealthRecords() {
  try {
    utils.showLoading();

    // Try to get health records from API
    const filterPatientId = document.getElementById("filterPatientId").value;

    let healthRecords = [];
    if (filterPatientId) {
      healthRecords = await api.healthRecords.getByPatient(filterPatientId);
    } else {
      // Try to get all records
      try {
        healthRecords = await api.healthRecords.list();
      } catch (error) {
        console.log("List endpoint not available, showing empty list");
        healthRecords = [];
      }
    }

    allHealthRecords = healthRecords;
    renderHealthRecordsTable(healthRecords);
  } catch (error) {
    utils.showError("Failed to load health records: " + error.message);
    document.getElementById("healthRecordsTableBody").innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-danger">
                    <i class="fas fa-exclamation-triangle"></i> Failed to load health records
                </td>
            </tr>
        `;
  } finally {
    utils.hideLoading();
  }
}

// Handle Scan & Fill (upload image to backend OCR endpoint and fill form)
async function handleScanAndFill(e) {
  e.preventDefault();
  const patientId = document.getElementById("patientId").value.trim();
  if (!patientId) {
    utils.showError("Please enter Patient ID before scanning");
    return;
  }

  const input = document.getElementById("prescriptionImage");
  if (!input || !input.files || input.files.length === 0) {
    utils.showError("Please upload or choose an image file first");
    return;
  }

  const file = input.files[0];
  const fd = new FormData();
  fd.append("file", file, file.name);

  try {
    utils.showLoading();
    const resp = await fetch(`/api/health-records/${encodeURIComponent(patientId)}/scan`, {
      method: "POST",
      body: fd,
    });

    if (!resp.ok) {
      const txt = await resp.text();
      throw new Error(txt || `Server responded ${resp.status}`);
    }

    const payload = await resp.json();

    if (!payload || !payload.success) {
      throw new Error(payload.error || "Failed to extract data from image");
    }

    const data = payload.data || {};

    // Map known fields to form inputs
    // Set record type to Prescription
    document.getElementById("recordType").value = "Prescription";
    document.getElementById("title").value = data.patient_name
      ? `Prescription - ${data.patient_name}`
      : "Prescription";

    // Build content from available fields
    const parts = [];
    if (data.symptoms) parts.push(`Symptoms: ${data.symptoms}`);
    if (data.prescription) parts.push(`Prescription: ${data.prescription}`);
    if (data.dosage) parts.push(`Dosage: ${data.dosage}`);
    if (data.doctor_notes) parts.push(`Notes: ${data.doctor_notes}`);

    document.getElementById("content").value = parts.join("\n\n") || "";

    if (data.doctor_name) {
      document.getElementById("doctorName").value = data.doctor_name;
    }

    utils.showSuccess("Form auto-filled from image OCR. Please review before saving.");
    // show preview if available
    try {
      const preview = document.getElementById('prescriptionPreview');
      const img = document.getElementById('prescriptionPreviewImg');
      if (preview && img && input.files && input.files[0]) {
        img.src = URL.createObjectURL(input.files[0]);
        preview.style.display = 'block';
      }
    } catch (err) {
      // ignore preview errors
    }
  } catch (error) {
    utils.showError("Scan failed: " + (error.message || error));
  } finally {
    utils.hideLoading();
  }
}

// Render health records table
function renderHealthRecordsTable(healthRecords) {
  const tbody = document.getElementById("healthRecordsTableBody");
  document.getElementById("recordCount").textContent = healthRecords.length;

  if (healthRecords.length === 0) {
    tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted">
                    <i class="fas fa-inbox"></i> No health records found. Create one above or filter by patient ID.
                </td>
            </tr>
        `;
    return;
  }

  tbody.innerHTML = healthRecords
    .map((record) => {
      // Handle both ISO and formatted dates
      const recordDate = record.date
        ? utils.formatDate(record.date)
        : utils.formatDate(record.receivedAt);
      const recordId = record.id || record.record_id;
      const patientName = record.patientName || "Unknown";
      const patientId = record.patientId || "Unknown";
      const title = record.title || record.type || "Record";
      const recordType = record.type || "N/A";

      // Extract doctor name from data if available
      const doctorName =
        (record.data &&
          (record.data.performedBy ||
            record.data.prescribedBy ||
            record.data.doctor_name)) ||
        "N/A";

      return `
            <tr>
                <td><small>${recordId}</small></td>
                <td>
                    <div>${patientName}</div>
                    <small class="text-muted">${patientId}</small>
                </td>
                <td>${title}</td>
                <td><span class="badge bg-info">${recordType}</span></td>
                <td>${recordDate}</td>
                <td>${doctorName}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="viewHealthRecord('${recordId}')">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `;
    })
    .join("");
}

// Handle create health record form submission
async function handleCreateHealthRecord(e) {
  e.preventDefault();

  // Simple validation
  const patientId = document.getElementById("patientId").value.trim();
  const recordType = document.getElementById("recordType").value;
  const recordDate = document.getElementById("recordDate").value;
  const title = document.getElementById("title").value.trim();

  if (!patientId || !recordType || !recordDate || !title) {
    utils.showError("Please fill in all required fields");
    return;
  }

  try {
    utils.showLoading();

    // Simple API call
    await api.healthRecords.create({
      patientId,
      recordType,
      recordDate,
      title,
      content: document.getElementById("content").value.trim() || null,
      doctorName: document.getElementById("doctorName").value.trim() || null,
      department: document.getElementById("department").value.trim() || null,
      fileUrl: document.getElementById("fileUrl").value.trim() || null,
    });

    utils.showSuccess("Health record created successfully!");
    e.target.reset();
    document.getElementById("recordDate").value = new Date()
      .toISOString()
      .split("T")[0];
    await loadHealthRecords();
  } catch (error) {
    utils.showError("Failed to create health record: " + error.message);
  } finally {
    utils.hideLoading();
  }
}

// Handle patient search
async function handleSearchPatient() {
  const mobile = document.getElementById("searchMobile").value;

  if (!mobile || mobile.length !== 10) {
    utils.showError("Please enter a valid 10-digit mobile number");
    return;
  }

  try {
    utils.showLoading();
    const patient = await api.patients.search(mobile);

    if (patient) {
      document.getElementById("searchResults").innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <h6>${patient.name}</h6>
                        <p class="mb-2">
                            <strong>Patient ID:</strong> ${patient.patient_id}<br>
                            <strong>Mobile:</strong> ${patient.mobile_number}
                        </p>
                        <button class="btn btn-sm btn-primary" onclick="selectPatient('${patient.patient_id}', '${patient.name}')">
                            <i class="fas fa-check"></i> Select Patient
                        </button>
                    </div>
                </div>
            `;
    } else {
      document.getElementById("searchResults").innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i> No patient found with this mobile number
                </div>
            `;
    }
  } catch (error) {
    utils.showError("Search failed: " + error.message);
  } finally {
    utils.hideLoading();
  }
}

// Select patient from search
function selectPatient(patientId, patientName) {
  document.getElementById("patientId").value = patientId;
  const modal = bootstrap.Modal.getInstance(
    document.getElementById("patientSearchModal"),
  );
  modal.hide();
  utils.showSuccess(`Selected patient: ${patientName}`);
}

// Apply filters
async function applyFilters() {
  const patientId = document.getElementById("filterPatientId").value;
  const recordType = document.getElementById("filterRecordType").value;
  const startDate = document.getElementById("filterStartDate").value;
  const endDate = document.getElementById("filterEndDate").value;

  // If patient ID is specified, fetch records for that patient
  if (patientId) {
    try {
      utils.showLoading();
      const healthRecords = await api.healthRecords.getByPatient(patientId);
      allHealthRecords = healthRecords;

      // Apply additional filters
      let filteredRecords = [...healthRecords];

      if (recordType) {
        filteredRecords = filteredRecords.filter(
          (r) => r.record_type === recordType,
        );
      }

      if (startDate) {
        filteredRecords = filteredRecords.filter(
          (r) => r.record_date >= startDate,
        );
      }

      if (endDate) {
        filteredRecords = filteredRecords.filter(
          (r) => r.record_date <= endDate,
        );
      }

      renderHealthRecordsTable(filteredRecords);
    } catch (error) {
      utils.showError("Failed to apply filters: " + error.message);
    } finally {
      utils.hideLoading();
    }
  } else {
    // Apply filters on current list
    let filteredRecords = [...allHealthRecords];

    if (recordType) {
      filteredRecords = filteredRecords.filter(
        (r) => r.record_type === recordType,
      );
    }

    if (startDate) {
      filteredRecords = filteredRecords.filter(
        (r) => r.record_date >= startDate,
      );
    }

    if (endDate) {
      filteredRecords = filteredRecords.filter((r) => r.record_date <= endDate);
    }

    renderHealthRecordsTable(filteredRecords);
  }
}

// Clear filters
function clearFilters() {
  document.getElementById("filterPatientId").value = "";
  document.getElementById("filterRecordType").value = "";
  document.getElementById("filterStartDate").value = "";
  document.getElementById("filterEndDate").value = "";
  loadHealthRecords();
}

// View health record details
async function viewHealthRecord(recordId) {
  try {
    utils.showLoading();

    // Find record in current list
    const record = allHealthRecords.find(
      (r) => (r.record_id || r.id) === recordId,
    );

    if (!record) {
      utils.showError("Health record not found");
      return;
    }

    currentRecord = record;

    // Populate modal
    document.getElementById("detailRecordId").textContent =
      record.record_id || record.id;
    document.getElementById("detailRecordType").textContent =
      record.record_type || "N/A";
    document.getElementById("detailPatientId").textContent = record.patient_id;
    document.getElementById("detailPatientName").textContent =
      record.patient_name || "N/A";
    document.getElementById("detailVisitId").textContent =
      record.visit_id || "N/A";
    document.getElementById("detailContextId").textContent =
      record.context_id || "N/A";
    document.getElementById("detailRecordDate").textContent = utils.formatDate(
      record.record_date,
    );
    document.getElementById("detailTitle").textContent = record.title;
    document.getElementById("detailDoctorName").textContent =
      record.doctor_name || "N/A";
    document.getElementById("detailDepartment").textContent =
      record.department || "N/A";
    document.getElementById("detailContent").textContent =
      record.content || "No content provided";
    document.getElementById("detailCreatedAt").textContent = utils.formatDate(
      record.created_at,
    );
    document.getElementById("detailUpdatedAt").textContent = utils.formatDate(
      record.updated_at,
    );

    // Show/hide file URL
    if (record.file_url) {
      document.getElementById("fileUrlSection").style.display = "block";
      document.getElementById("detailFileUrl").href = record.file_url;
    } else {
      document.getElementById("fileUrlSection").style.display = "none";
    }

    // Show modal
    const modal = new bootstrap.Modal(
      document.getElementById("recordDetailsModal"),
    );
    modal.show();
  } catch (error) {
    utils.showError("Failed to load health record details: " + error.message);
  } finally {
    utils.hideLoading();
  }
}

// Make functions globally accessible
window.viewHealthRecord = viewHealthRecord;
window.selectPatient = selectPatient;
