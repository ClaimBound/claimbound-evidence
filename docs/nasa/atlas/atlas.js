(() => {
  "use strict";

  const atlas = window.NASA_ATLAS_DATA;
  if (!atlas || !Array.isArray(atlas.cards)) {
    throw new Error("NASA atlas data did not load.");
  }

  const repositoryRoot = "https://github.com/ClaimBound/claimbound-evidence/blob/main/";
  const elements = {
    form: document.querySelector("#filters"),
    batch: document.querySelector("#batch-filter"),
    status: document.querySelector("#status-filter"),
    slot: document.querySelector("#slot-filter"),
    gaps: document.querySelector("#gaps-button"),
    reset: document.querySelector("#reset-button"),
    summary: document.querySelector("#result-summary"),
    header: document.querySelector("#slot-header"),
    heatmap: document.querySelector("#heatmap"),
    detailPanel: document.querySelector("#detail-panel"),
    detailTitle: document.querySelector("#detail-title"),
    detailEmpty: document.querySelector("#detail-empty"),
    detailContent: document.querySelector("#detail-content"),
    detailStatus: document.querySelector("#detail-status"),
    detailProtocol: document.querySelector("#detail-protocol"),
    detailSlot: document.querySelector("#detail-slot"),
    detailTopic: document.querySelector("#detail-topic"),
    detailClaim: document.querySelector("#detail-claim"),
    detailMissingRow: document.querySelector("#detail-missing-row"),
    detailMissing: document.querySelector("#detail-missing"),
    detailSource: document.querySelector("#detail-source"),
    detailSnapshot: document.querySelector("#detail-snapshot"),
    detailJson: document.querySelector("#detail-json"),
    detailSvg: document.querySelector("#detail-svg"),
  };

  let selectedProtocol = null;

  function appendOption(select, value, label) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    select.append(option);
  }

  function initializeFilters() {
    atlas.batches.forEach((batch) => {
      appendOption(
        elements.batch,
        String(batch.issue_number),
        `#${batch.issue_number} · ${batch.label}`,
      );
    });
    atlas.slot_labels.forEach((slot) => {
      appendOption(elements.slot, String(slot.slot), `${String(slot.slot).padStart(2, "0")} · ${slot.label}`);
    });
  }

  function renderHeader() {
    const label = document.createElement("span");
    label.className = "slot-header__label";
    label.textContent = "Mission / slot";
    elements.header.append(label);

    atlas.slot_labels.forEach((slot) => {
      const item = document.createElement("span");
      item.className = "slot-header__slot";
      item.textContent = String(slot.slot).padStart(2, "0");
      item.title = slot.label;
      elements.header.append(item);
    });
  }

  function currentFilters() {
    return {
      issue: elements.batch.value,
      status: elements.status.value,
      slot: elements.slot.value,
    };
  }

  function matches(card, filters) {
    return (
      (filters.issue === "all" || String(card.issue_number) === filters.issue) &&
      (filters.status === "all" || card.result_status === filters.status) &&
      (filters.slot === "all" || String(card.slot) === filters.slot)
    );
  }

  function makeCell(card, visible) {
    if (!visible) {
      const placeholder = document.createElement("span");
      placeholder.className = "cell-placeholder";
      placeholder.setAttribute("aria-hidden", "true");
      return placeholder;
    }

    const limited = card.result_status === "INSUFFICIENT_COVERAGE";
    const cell = document.createElement("button");
    cell.type = "button";
    cell.className = `cell${limited ? " cell--limited" : ""}`;
    cell.dataset.protocol = card.protocol_id;
    cell.textContent = String(card.slot).padStart(2, "0");
    cell.setAttribute("aria-pressed", String(card.protocol_id === selectedProtocol));
    cell.setAttribute(
      "aria-label",
      `${card.mission}, slot ${String(card.slot).padStart(2, "0")}, ${card.topic}: ${limited ? "limited coverage" : "passed under protocol"}`,
    );
    cell.addEventListener("click", () => selectCard(card));
    return cell;
  }

  function render() {
    const filters = currentFilters();
    const visibleCards = atlas.cards.filter((card) => matches(card, filters));
    elements.heatmap.replaceChildren();

    atlas.batches.forEach((batch) => {
      if (filters.issue !== "all" && filters.issue !== String(batch.issue_number)) {
        return;
      }

      const batchCards = visibleCards.filter((card) => card.issue_number === batch.issue_number);
      if (batchCards.length === 0) {
        return;
      }

      const group = document.createElement("section");
      group.className = "batch-group";
      group.setAttribute("aria-labelledby", `batch-${batch.issue_number}`);

      const heading = document.createElement("h3");
      heading.className = "batch-heading";
      heading.id = `batch-${batch.issue_number}`;
      heading.textContent = `Issue #${batch.issue_number} · ${batch.label}`;
      group.append(heading);

      batch.missions.forEach((mission) => {
        const missionCards = atlas.cards.filter(
          (card) => card.issue_number === batch.issue_number && card.mission === mission,
        );
        const visibleMissionCards = missionCards.filter((card) => matches(card, filters));
        if (visibleMissionCards.length === 0) {
          return;
        }

        const row = document.createElement("div");
        row.className = "mission-row";
        const missionLabel = document.createElement("span");
        missionLabel.className = "mission-label";
        missionLabel.textContent = mission;
        missionLabel.title = mission;
        row.append(missionLabel);
        missionCards.forEach((card) => row.append(makeCell(card, matches(card, filters))));
        group.append(row);
      });

      elements.heatmap.append(group);
    });

    if (visibleCards.length === 0) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent = "No evidence cards match these filters.";
      elements.heatmap.append(empty);
    }

    const missionCount = new Set(visibleCards.map((card) => card.mission)).size;
    const limitedCount = visibleCards.filter(
      (card) => card.result_status === "INSUFFICIENT_COVERAGE",
    ).length;
    elements.summary.textContent = `Showing ${visibleCards.length} evidence ${visibleCards.length === 1 ? "card" : "cards"} across ${missionCount} ${missionCount === 1 ? "mission" : "missions"}${limitedCount ? ` · ${limitedCount} limited` : ""}.`;

    if (selectedProtocol && !visibleCards.some((card) => card.protocol_id === selectedProtocol)) {
      clearSelection();
    }
  }

  function clearSelection() {
    selectedProtocol = null;
    elements.detailTitle.textContent = "Choose any cell";
    elements.detailEmpty.hidden = false;
    elements.detailContent.hidden = true;
    document.querySelectorAll(".cell[aria-pressed='true']").forEach((cell) => {
      cell.setAttribute("aria-pressed", "false");
    });
  }

  function selectCard(card) {
    selectedProtocol = card.protocol_id;
    document.querySelectorAll(".cell").forEach((cell) => {
      cell.setAttribute("aria-pressed", String(cell.dataset.protocol === selectedProtocol));
    });

    const limited = card.result_status === "INSUFFICIENT_COVERAGE";
    elements.detailTitle.textContent = card.mission;
    elements.detailEmpty.hidden = true;
    elements.detailContent.hidden = false;
    elements.detailStatus.className = `status-chip${limited ? " status-chip--limited" : ""}`;
    elements.detailStatus.textContent = limited ? "Limited coverage" : "Passed under protocol";
    elements.detailProtocol.textContent = card.protocol_id;
    elements.detailSlot.textContent = `${String(card.slot).padStart(2, "0")} · ${card.slot_label}`;
    elements.detailTopic.textContent = card.topic;
    elements.detailClaim.textContent = card.claim;
    elements.detailMissingRow.hidden = !limited;
    elements.detailMissing.textContent = card.missing_patterns.join(", ") || "None recorded";
    elements.detailSource.textContent = card.official_source_name;
    elements.detailSource.href = card.official_source_url;
    elements.detailSnapshot.textContent = `${card.access_date} · SHA-256 ${card.source_sha256 || "not recorded"}`;
    elements.detailJson.href = repositoryRoot + card.evidence_path;
    elements.detailSvg.href = repositoryRoot + card.svg_path;
  }

  elements.form.addEventListener("change", render);
  elements.form.addEventListener("reset", () => {
    window.setTimeout(() => {
      clearSelection();
      render();
    }, 0);
  });
  elements.gaps.addEventListener("click", () => {
    elements.status.value = "INSUFFICIENT_COVERAGE";
    elements.batch.value = "all";
    elements.slot.value = "all";
    render();
  });

  initializeFilters();
  renderHeader();
  render();
})();
