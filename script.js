//console script - paste this code into the dev tools console on web

(function() {
    function getReactHandler() {
        const app = document.querySelector("#app > div > div");
        if (!app) return null;
        return Object.values(app).find(x => x && x.children && x.children[1] && x.children[1]._owner)?._owner;
    }

    function autoAnswer() {
        const handler = getReactHandler();
        if (!handler) {
            console.log("❌ Cannot find game data. Make sure you are inside a question screen!");
            return;
        }

        const gameState = handler.stateNode?.state;
        if (!gameState || !gameState.question) {
            console.log("❌ Cannot read game state or no question yet!");
            return;
        }

        console.log("📖 Question:", gameState.question);
        console.log("✅ Correct Answer(s):", gameState.correctAnswers);
        console.log("🧩 Choices:", gameState.choices);

        const choicesElements = document.querySelectorAll('[class*="answerContainer"]');
        if (choicesElements.length === 0) {
            console.log("❌ No answer buttons found on screen!");
            return;
        }

        for (let choice of choicesElements) {
            if (gameState.correctAnswers.some(ans => choice.innerText.includes(ans))) {
                console.log("🎯 Clicking correct answer:", choice.innerText);
                choice.click();
                return;
            }
        }

        console.log("❓ Couldn't find the correct button to click.");
    }

    console.log("🚀 Auto-Answer script loaded! Running every 1 second...");
    setInterval(autoAnswer, 1000);
})();
