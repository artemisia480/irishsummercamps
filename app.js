const campListEl = document.getElementById("campList");
const template = document.getElementById("campCardTemplate");
const searchInput = document.getElementById("searchInput");
const countyFilter = document.getElementById("countyFilter");
const foodFilter = document.getElementById("foodFilter");
const minAgeFilter = document.getElementById("minAgeFilter");
const maxPriceFilter = document.getElementById("maxPriceFilter");
const weekFilter = document.getElementById("weekFilter");
const clearFiltersBtn = document.getElementById("clearFiltersBtn");
const resultsCount = document.getElementById("resultsCount");
const submissionForm = document.getElementById("submissionForm");
const submissionMessage = document.getElementById("submissionMessage");

let allCamps = [];

function formatPrice(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "Check source";
  }
  return new Intl.NumberFormat("en-IE", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(value);
}

/** Normalize age for display: integers only, no leading zeros (6 not 06). */
function parseDisplayAge(value) {
  if (value === null || value === undefined || value === "") {
    return NaN;
  }
  const n = Number(value);
  if (!Number.isFinite(n)) {
    return NaN;
  }
  return Math.round(n);
}

function formatAgeRange(camp) {
  const min = parseDisplayAge(camp.ageMin);
  const max = parseDisplayAge(camp.ageMax);
  const hasMin = Number.isFinite(min);
  const hasMax = Number.isFinite(max);
  if (hasMin && hasMax) {
    return `${min}–${max}`;
  }
  if (hasMin) {
    return `${min}+`;
  }
  if (hasMax) {
    return `Up to ${max}`;
  }
  return "Check source";
}

/**
 * Standardize hours text: pad times to HH:MM, unify dash between ranges.
 * Leaves words like "Morning", "Varies", etc. unchanged when no time tokens match.
 */
function formatHoursDisplay(raw) {
  if (raw === null || raw === undefined) {
    return "Check source";
  }
  const text = String(raw).trim();
  if (!text) {
    return "Check source";
  }

  let out = text.replace(/\s+/g, " ");

  // Normalize 24h-style times: 9:30 -> 09:30, 09:5 -> pad minutes (guard invalid)
  out = out.replace(/\b(\d{1,2}):(\d{2})\b/g, (_, h, m) => {
    let hh = parseInt(h, 10);
    let mm = parseInt(m, 10);
    if (hh > 23 || mm > 59) {
      return `${h}:${m}`;
    }
    return `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}`;
  });

  // Unify range separators: hyphen / en-dash / em-dash -> en-dash with spaces
  out = out.replace(/\s*[\u2013\u2014\-]\s*/g, " – ");

  return out;
}

function formatExtendedHoursDisplay(raw) {
  if (raw === null || raw === undefined || String(raw).trim() === "") {
    return "Not listed";
  }
  return formatHoursDisplay(raw);
}

function renderCamps(camps) {
  campListEl.innerHTML = "";
  resultsCount.textContent = `${camps.length} camp(s) found`;

  if (camps.length === 0) {
    campListEl.innerHTML = "<p>No camps found. Try adjusting your filters.</p>";
    return;
  }

  camps.forEach((camp) => {
    try {
      const fragment = template.content.cloneNode(true);
      fragment.querySelector(".camp-name").textContent = camp.name || "Camp";
      fragment.querySelector(".camp-summary").textContent = camp.type || "Camp details";
      fragment.querySelector(".camp-county").textContent = camp.county || "Unknown";
      fragment.querySelector(".camp-location").textContent = camp.locationDetail || "Check source";
      fragment.querySelector(".camp-age").textContent = formatAgeRange(camp);
      fragment.querySelector(".camp-price").textContent = formatPrice(camp.priceEur);
      fragment.querySelector(".camp-hours").textContent = formatHoursDisplay(camp.hours);
      fragment.querySelector(".camp-extended").textContent = formatExtendedHoursDisplay(camp.extendedHours);
      fragment.querySelector(".camp-weeks").textContent =
        Array.isArray(camp.campWeeks) && camp.campWeeks.length > 0
          ? camp.campWeeks.join(", ")
          : "Not listed";
      fragment.querySelector(".camp-food").textContent =
        camp.foodProvided === true ? "Yes" : camp.foodProvided === false ? "No" : "Unknown";

      const linkEl = fragment.querySelector(".camp-book-link");
      if (camp.sourceUrl) {
        linkEl.href = camp.sourceUrl;
      } else {
        linkEl.removeAttribute("href");
        linkEl.textContent = "No booking link yet";
        linkEl.classList.add("disabled");
        linkEl.setAttribute("aria-disabled", "true");
      }
      campListEl.appendChild(fragment);
    } catch (error) {
      // Skip malformed camp records so one bad row does not break the full listing.
      console.error("Failed to render camp card", camp, error);
    }
  });
}

function getFilteredCamps() {
  const nameQuery = searchInput.value.trim().toLowerCase();
  const county = countyFilter.value;
  const food = foodFilter.value;
  const minAge = Number(minAgeFilter.value);
  const maxPrice = Number(maxPriceFilter.value);
  const selectedWeek = weekFilter.value;

  return allCamps.filter((camp) => {
    const searchableText = `${camp.name || ""} ${camp.type || ""} ${camp.locationDetail || ""}`.toLowerCase();
    const nameMatch = searchableText.includes(nameQuery);
    const countyMatch = !county || camp.county === county;
    const foodMatch =
      !food ||
      (food === "yes" && camp.foodProvided) ||
      (food === "no" && !camp.foodProvided);
    const campMinAge = parseDisplayAge(camp.ageMin);
    const ageMatch = !minAge || !Number.isFinite(campMinAge) || campMinAge <= minAge;
    const priceMatch = !maxPrice || camp.priceEur === null || camp.priceEur === undefined || camp.priceEur <= maxPrice;
    const weeks = Array.isArray(camp.campWeeks) ? camp.campWeeks : [];
    const weekMatch = !selectedWeek || weeks.includes(selectedWeek);

    return nameMatch && countyMatch && foodMatch && ageMatch && priceMatch && weekMatch;
  });
}

function applyFilters() {
  renderCamps(getFilteredCamps());
}

function fillCountyOptions(camps) {
  const counties = [...new Set(camps.map((camp) => camp.county))].sort();
  counties.forEach((county) => {
    const option = document.createElement("option");
    option.value = county;
    option.textContent = county;
    countyFilter.appendChild(option);
  });
}

function resetFilters() {
  searchInput.value = "";
  countyFilter.value = "";
  foodFilter.value = "";
  minAgeFilter.value = "";
  maxPriceFilter.value = "";
  weekFilter.value = "";
  applyFilters();
}

async function init() {
  try {
    const response = await fetch("/api/camps");
    if (!response.ok) {
      throw new Error("Could not load camp data.");
    }
    allCamps = await response.json();
    fillCountyOptions(allCamps);
    applyFilters();
  } catch (error) {
    campListEl.innerHTML = `<p>${error.message}</p>`;
  }
}

function parseOptionalNumber(value) {
  if (value === "" || value === null || value === undefined) {
    return null;
  }
  const parsed = Number(value);
  return Number.isNaN(parsed) ? null : parsed;
}

async function handleSubmission(event) {
  event.preventDefault();
  submissionMessage.textContent = "";

  const formData = new FormData(submissionForm);
  const payload = {
    name: formData.get("name"),
    type: formData.get("type"),
    county: formData.get("county"),
    locationDetail: formData.get("locationDetail"),
    hours: formData.get("hours"),
    extendedHours: formData.get("extendedHours"),
    campWeeksText: formData.get("campWeeksText"),
    priceEur: parseOptionalNumber(formData.get("priceEur")),
    ageMin: parseOptionalNumber(formData.get("ageMin")),
    ageMax: parseOptionalNumber(formData.get("ageMax")),
    foodProvided: formData.get("foodProvided"),
    sourceUrl: formData.get("sourceUrl"),
    contactName: formData.get("contactName"),
    contactEmail: formData.get("contactEmail"),
    notes: formData.get("notes"),
  };

  try {
    const response = await fetch("/api/submissions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Could not submit camp.");
    }
    submissionForm.reset();
    submissionMessage.textContent = "Thank you. Your submission is pending review.";
  } catch (error) {
    submissionMessage.textContent = error.message;
  }
}

[
  searchInput,
  countyFilter,
  foodFilter,
  minAgeFilter,
  maxPriceFilter,
  weekFilter,
].forEach((input) => {
  input.addEventListener("input", applyFilters);
  input.addEventListener("change", applyFilters);
});

clearFiltersBtn.addEventListener("click", resetFilters);
submissionForm.addEventListener("submit", handleSubmission);
init();
