const state = {
    stores: [],
    selectedSet: new Set(),
    completedStores: [],
    processedStores: [],
    activeTab: "stores",
    currentJobId: null,
    currentJobType: null,
    pollingHandle: null,
};

function qs(id) {
    return document.getElementById(id);
}

async function fetchJson(url, options = {}) {
    const response = await fetch(url, options);
    const text = await response.text();
    let data = null;
    try {
        data = text ? JSON.parse(text) : {};
    } catch (error) {
        const snippet = text ? text.slice(0, 160) : "";
        throw new Error(`サーバーが JSON 以外を返しました (${response.status}): ${snippet}`);
    }
    if (!response.ok) {
        throw new Error(data.error || "通信に失敗しました");
    }
    return data;
}

function showAlert(message, type) {
    const alertEl = qs("alert");
    alertEl.textContent = message;
    alertEl.className = `alert ${type}`;
    if (type === "success") {
        setTimeout(() => {
            alertEl.className = "alert";
        }, 5000);
    }
}

function switchMainTab(tabName) {
    state.activeTab = tabName;
    qs("storesTabBtn").classList.toggle("active", tabName === "stores");
    qs("logsTabBtn").classList.toggle("active", tabName === "logs");
    qs("storesPanel").classList.toggle("active", tabName === "stores");
    qs("logsPanel").classList.toggle("active", tabName === "logs");
}

function setLatestLog({ title = "実行ログ", body = "", status = "idle", meta = "" }) {
    qs("logTitle").textContent = title;
    qs("logMeta").textContent = meta || "まだジョブは実行されていません。";
    const statusLabel = {
        idle: "待機中",
        queued: "受付済み",
        running: "実行中",
        succeeded: "成功",
        failed: "失敗",
    };
    const logStatus = qs("logStatus");
    logStatus.textContent = statusLabel[status] || "待機中";
    logStatus.className = `log-status${status === "idle" ? "" : ` ${status}`}`;
    qs("logOutput").textContent = body && String(body).trim() ? String(body).trim() : "まだ実行ログはありません。";
}

function setLoading(isVisible, text = "", meta = "") {
    qs("loading").style.display = isVisible ? "flex" : "none";
    qs("loadingText").textContent = text || "処理を実行中...";
    qs("jobMeta").textContent = meta || "";
}

function updateStatus() {
    const selectedCount = state.selectedSet.size;
    qs("selectedCount").textContent = String(selectedCount);
    qs("totalCount").textContent = String(state.stores.length);
    qs("submitBtn").disabled = selectedCount === 0 || Boolean(state.currentJobId);
    qs("formatBtn").disabled = Boolean(state.currentJobId);
    qs("saveOrderBtn").disabled = state.stores.length === 0 || Boolean(state.currentJobId);
    qs("jobStatusSummary").textContent = state.currentJobId ? "ジョブ実行中" : "ジョブ待機中";
}

function isTestModeEnabled() {
    return Boolean(qs("testModeToggle")?.checked);
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function isValidStoreUrl(value) {
    try {
        const parsed = new URL(String(value || "").trim());
        return parsed.protocol === "http:" || parsed.protocol === "https:";
    } catch (error) {
        return false;
    }
}

function renderStoreList() {
    const container = qs("storeListContainer");
    if (state.stores.length === 0) {
        container.innerHTML = '<div class="empty-message">店舗情報が見つかりませんでした</div>';
        updateStatus();
        return;
    }

    container.innerHTML = state.stores.map((store, index) => {
        const itemClasses = ["store-item"];
        if (state.completedStores.includes(store.name)) itemClasses.push("completed");
        else if (state.processedStores.includes(store.name)) itemClasses.push("processed");
        const checked = state.selectedSet.has(store.name) ? "checked" : "";
        return `
            <div class="${itemClasses.join(" ")}" draggable="true" data-index="${index}">
                <div class="drag-handle" title="ドラッグで並び替え"></div>
                <input class="store-checkbox" type="checkbox" data-store-name="${escapeHtml(store.name)}" ${checked}>
                <label class="store-label">${escapeHtml(store.name)}</label>
                <button class="store-edit-btn" type="button" data-edit-store="${escapeHtml(store.name)}">URL変更</button>
                <button class="store-delete-btn" type="button" data-delete-store="${escapeHtml(store.name)}">削除</button>
            </div>
        `;
    }).join("");

    container.querySelectorAll(".store-checkbox").forEach((checkbox) => {
        checkbox.addEventListener("change", (event) => {
            const storeName = event.currentTarget.dataset.storeName;
            if (event.currentTarget.checked) {
                state.selectedSet.add(storeName);
            } else {
                state.selectedSet.delete(storeName);
            }
            updateStatus();
        });
    });

    container.querySelectorAll("[data-edit-store]").forEach((button) => {
        button.addEventListener("click", (event) => updateStoreUrl(event.currentTarget.dataset.editStore, event));
    });

    container.querySelectorAll("[data-delete-store]").forEach((button) => {
        button.addEventListener("click", (event) => deleteStore(event.currentTarget.dataset.deleteStore, event));
    });

    initDragAndDrop();
    updateStatus();
}

function initDragAndDrop() {
    const items = qs("storeListContainer").querySelectorAll(".store-item");
    items.forEach((item) => {
        item.addEventListener("dragstart", (event) => {
            event.dataTransfer.setData("text/plain", event.currentTarget.dataset.index);
        });
        item.addEventListener("dragover", (event) => {
            event.preventDefault();
            event.currentTarget.classList.add("dragover");
        });
        item.addEventListener("dragleave", (event) => {
            event.currentTarget.classList.remove("dragover");
        });
        item.addEventListener("drop", (event) => {
            event.preventDefault();
            event.currentTarget.classList.remove("dragover");
            const from = Number(event.dataTransfer.getData("text/plain"));
            const to = Number(event.currentTarget.dataset.index);
            if (Number.isNaN(from) || Number.isNaN(to) || from === to) return;
            const moved = state.stores.splice(from, 1)[0];
            state.stores.splice(to, 0, moved);
            renderStoreList();
        });
    });
}

async function loadSettings() {
    const settings = await fetchJson("/api/settings");
    qs("htmlOutputDir").value = settings.html_output_dir || "";
    qs("csvOutputDir").value = settings.csv_output_dir || "";
    qs("storeListPath").value = settings.store_list_path || "";
    qs("tempStoreListInfo").textContent = `一時選択CSV: ${settings.temp_store_list_path || ""}`;
}

async function loadStores() {
    await loadSettings();
    state.stores = await fetchJson("/api/stores");
    state.selectedSet = new Set([...state.selectedSet].filter((name) => state.stores.some((store) => store.name === name)));
    renderStoreList();
}

async function addStore() {
    const storeName = qs("newStoreName").value.trim();
    const storeUrl = qs("newStoreUrl").value.trim();
    if (!storeName) {
        showAlert("店舗名を入力してください", "error");
        return;
    }
    if (!storeUrl) {
        showAlert("店舗URLを入力してください", "error");
        return;
    }
    if (!isValidStoreUrl(storeUrl)) {
        showAlert("店舗URLの形式が不正です", "error");
        return;
    }

    qs("addStoreBtn").disabled = true;
    try {
        const result = await fetchJson("/api/stores", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ store_name: storeName, store_url: storeUrl }),
        });
        qs("newStoreName").value = "";
        qs("newStoreUrl").value = "";
        showAlert(result.message || "店舗を追加しました", "success");
        await loadStores();
    } catch (error) {
        showAlert(`エラー: ${error.message}`, "error");
    } finally {
        qs("addStoreBtn").disabled = false;
    }
}

async function deleteStore(storeName, event) {
    event.preventDefault();
    event.stopPropagation();
    if (!confirm(`「${storeName}」をリストから削除しますか？`)) {
        return;
    }

    try {
        const result = await fetchJson(`/api/stores/${encodeURIComponent(storeName)}`, {
            method: "DELETE",
        });
        state.selectedSet.delete(storeName);
        state.completedStores = state.completedStores.filter((name) => name !== storeName);
        state.processedStores = state.processedStores.filter((name) => name !== storeName);
        showAlert(result.message || "店舗を削除しました", "success");
        await loadStores();
    } catch (error) {
        showAlert(`エラー: ${error.message}`, "error");
    }
}

async function updateStoreUrl(storeName, event) {
    event.preventDefault();
    event.stopPropagation();

    const store = state.stores.find((item) => item.name === storeName);
    const nextUrl = prompt(`「${storeName}」の新しい店舗URLを入力してください`, store?.url || "");
    if (nextUrl === null) {
        return;
    }

    const trimmedUrl = nextUrl.trim();
    if (!trimmedUrl) {
        showAlert("店舗URLを入力してください", "error");
        return;
    }
    if (!isValidStoreUrl(trimmedUrl)) {
        showAlert("店舗URLの形式が不正です", "error");
        return;
    }

    try {
        const result = await fetchJson(`/api/stores/${encodeURIComponent(storeName)}/url`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ store_url: trimmedUrl }),
        });
        showAlert(result.message || "店舗URLを更新しました", "success");
        await loadStores();
    } catch (error) {
        showAlert(`エラー: ${error.message}`, "error");
    }
}

async function saveSettings() {
    qs("saveSettingsBtn").disabled = true;
    try {
        const result = await fetchJson("/api/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                html_output_dir: qs("htmlOutputDir").value.trim(),
                csv_output_dir: qs("csvOutputDir").value.trim(),
            }),
        });
        showAlert(result.message || "設定を保存しました", "success");
        await loadStores();
    } catch (error) {
        showAlert(`エラー: ${error.message}`, "error");
    } finally {
        qs("saveSettingsBtn").disabled = false;
    }
}

async function saveOrder() {
    qs("saveOrderBtn").disabled = true;
    try {
        const result = await fetchJson("/api/stores/reorder", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ order: state.stores.map((store) => store.name) }),
        });
        showAlert(result.message || "並び順を保存しました", "success");
        await loadStores();
    } catch (error) {
        showAlert(`エラー: ${error.message}`, "error");
    } finally {
        qs("saveOrderBtn").disabled = false;
    }
}

function resetJobState() {
    state.currentJobId = null;
    state.currentJobType = null;
    if (state.pollingHandle) {
        clearTimeout(state.pollingHandle);
        state.pollingHandle = null;
    }
    setLoading(false);
    updateStatus();
}

function startPollingJob(jobId, jobType) {
    state.currentJobId = jobId;
    state.currentJobType = jobType;
    updateStatus();

    const testScrapeEnabled = jobType === "scrape" && isTestModeEnabled();
    const title = jobType === "scrape" ? "スクレイピング実行" : "Excel 自動整形";
    const loadingText = jobType === "scrape"
        ? (testScrapeEnabled ? "テストスクレイピングを実行中...（直近3日分）" : "スクレイピング処理を実行中...")
        : "Excel 自動整形を実行中...";
    setLoading(true, loadingText, `job_id: ${jobId}`);
    setLatestLog({
        title,
        body: testScrapeEnabled
            ? "テストスクレイピングを開始しました。直近3日分のみ取得します。"
            : "ジョブを開始しました。結果を待っています。",
        status: "queued",
        meta: `job_id: ${jobId}`,
    });

    const poll = async () => {
        try {
            const result = await fetchJson(`/api/jobs/${jobId}`);
            const currentTestMode = jobType === "scrape" && Boolean(result.test_mode);
            const body = [result.message || "", result.output || ""].filter(Boolean).join("\n\n");
            setLatestLog({
                title,
                body,
                status: result.status,
                meta: `job_id: ${jobId} / started: ${result.started_at || "-"}${currentTestMode ? " / test mode" : ""}`,
            });

            if (result.status === "running" || result.status === "queued") {
                setLoading(
                    true,
                    currentTestMode ? "テストスクレイピングを実行中...（直近3日分）" : loadingText,
                    `job_id: ${jobId}${currentTestMode ? " / test mode" : ""}`
                );
                state.pollingHandle = setTimeout(poll, 1500);
                return;
            }

            if (jobType === "format") {
                state.completedStores = Array.isArray(result.completed_stores) ? result.completed_stores : [];
                state.processedStores = Array.isArray(result.processed_stores) ? result.processed_stores : [];
            }

            if (result.status === "succeeded") {
                showAlert(result.message || "処理が完了しました", "success");
            } else {
                showAlert(`エラー: ${result.message || "処理に失敗しました"}`, "error");
            }

            await loadStores();
            state.selectedSet.clear();
            resetJobState();
            renderStoreList();
        } catch (error) {
            showAlert(`エラー: ${error.message}`, "error");
            setLatestLog({
                title,
                body: error.message,
                status: "failed",
                meta: `job_id: ${jobId}`,
            });
            resetJobState();
        }
    };

    poll();
}

async function submitSelection() {
    if (state.selectedSet.size === 0) {
        showAlert("最低1つの店舗を選択してください", "error");
        return;
    }
    try {
        const result = await fetchJson("/api/scrape", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ stores: [...state.selectedSet], test_mode: isTestModeEnabled() }),
        });
        startPollingJob(result.job_id, "scrape");
    } catch (error) {
        showAlert(`エラー: ${error.message}`, "error");
        setLatestLog({
            title: "スクレイピング実行",
            body: error.message,
            status: "failed",
        });
    }
}

async function formatOffline() {
    try {
        const result = await fetchJson("/api/format-offline", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({}),
        });
        startPollingJob(result.job_id, "format");
    } catch (error) {
        showAlert(`エラー: ${error.message}`, "error");
        setLatestLog({
            title: "Excel 自動整形",
            body: error.message,
            status: "failed",
        });
    }
}

function selectAll() {
    state.selectedSet = new Set(state.stores.map((store) => store.name));
    renderStoreList();
}

function clearAll() {
    state.selectedSet.clear();
    renderStoreList();
}

function bindEvents() {
    qs("storesTabBtn").addEventListener("click", () => switchMainTab("stores"));
    qs("logsTabBtn").addEventListener("click", () => switchMainTab("logs"));
    qs("addStoreBtn").addEventListener("click", addStore);
    qs("saveSettingsBtn").addEventListener("click", saveSettings);
    qs("submitBtn").addEventListener("click", submitSelection);
    qs("formatBtn").addEventListener("click", formatOffline);
    qs("saveOrderBtn").addEventListener("click", saveOrder);
    qs("selectAllBtn").addEventListener("click", selectAll);
    qs("clearAllBtn").addEventListener("click", clearAll);
}

async function init() {
    bindEvents();
    setLatestLog({ title: "実行ログ", body: "", status: "idle" });
    try {
        await loadStores();
    } catch (error) {
        showAlert(`エラー: ${error.message}`, "error");
    }
}

document.addEventListener("DOMContentLoaded", init);
