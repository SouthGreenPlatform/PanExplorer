document.addEventListener("click", function (event) {

    const button = event.target.closest(".fullscreen-button");

    if (!button) {
        return;
    }

    const container = button.closest(".fullscreen-container");

    if (!container) {
        return;
    }

    if (!document.fullscreenElement) {

        container.requestFullscreen().catch(function (err) {
            console.error("Erreur fullscreen :", err);
        });

    } else {

        document.exitFullscreen();
    }
});


document.addEventListener("fullscreenchange", function () {

    const container = document.fullscreenElement;

    if (container) {

        // =========================
        // ENTRÉE EN FULLSCREEN
        // =========================

        const graph = container.querySelector(".dash-graph");

        if (!graph) {
            return;
        }

        // Sauvegarde de la hauteur normale
        graph.dataset.normalHeight = graph.style.height;

        // Le graphe prend toute la hauteur disponible
        graph.style.height = "100vh";

        // Redimensionnement Plotly
        setTimeout(function () {

            const plot = graph.querySelector(".js-plotly-plot");

            if (plot && typeof Plotly !== "undefined") {
                Plotly.Plots.resize(plot);
            }

        }, 200);

    } else {

        // =========================
        // SORTIE DU FULLSCREEN
        // =========================

        const graphs = document.querySelectorAll(
            ".fullscreen-container .dash-graph"
        );

        graphs.forEach(function (graph) {

            // Restaurer la hauteur originale
            if (graph.dataset.normalHeight) {
                graph.style.height = graph.dataset.normalHeight;
            }

            setTimeout(function () {

                const plot = graph.querySelector(".js-plotly-plot");

                if (plot && typeof Plotly !== "undefined") {
                    Plotly.Plots.resize(plot);
                }

            }, 200);
        });
    }
});