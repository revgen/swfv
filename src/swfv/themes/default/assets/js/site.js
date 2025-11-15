function onload() {
    const switchLabel = document.getElementById("toggleSwitchContainer");
    const checked = localStorage.getItem("mode") === "dark" ? "checked" : "";
    console.debug(`Read mode from the storage: darkModeCheckBox=${checked}`);
    switchLabel.innerHTML = `<input id="toggleSwitch" type="checkbox" ${checked} onclick="toggleMode();"><span class="slider round"></span>`;
    toggleMode(!!checked);
};

function toggleMode(darkMode) {
    console.debug(`Toggle page theme from ${document.body.classList} (darkMode=${darkMode})`);
    const classList = document.body.classList;
    const toggleSwitchEl = document.getElementById("toggleSwitch");
    if (darkMode === null || darkMode === undefined) {
        // switch light-mode -> dark-mode
        darkMode = classList.contains("light-mode");
        console.info(`Toggle to darkMode=${darkMode}`);
    }
    if (darkMode) {
        console.info(`Switch to dark mode`);
        classList.add("dark-mode");
        classList.remove("light-mode");
        toggleSwitchEl.checked = true;
        localStorage.setItem("mode", "dark");
        
    } else {
        console.info(`Switch to light mode`);
        classList.add("light-mode");
        classList.remove("dark-mode");
        toggleSwitchEl.checked = false;
        localStorage.setItem("mode", "light");
    }
};
