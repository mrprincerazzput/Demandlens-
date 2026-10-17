
document.addEventListener("DOMContentLoaded", function () {
    console.log("DemandLens JavaScript connected!");

    // =========================
    // 1. SEARCH AND FILTERS
    // =========================

    const searchInput = document.getElementById("productSearch");
    const categoryFilter = document.getElementById("categoryFilter");
    const tableBody = document.getElementById("productTable");

    if (searchInput && categoryFilter && tableBody) {

        // Create demand status dropdown
        const statusFilter = document.createElement("select");
        statusFilter.id = "demandFilter";

        statusFilter.innerHTML =
            '<option value="all">All Demand Levels</option>' +
            '<option value="high">High Demand</option>' +
            '<option value="medium">Stable Demand</option>' +
            '<option value="low">Low Demand</option>';

        statusFilter.style.padding = "12px";
        statusFilter.style.border = "1px solid #d5deec";
        statusFilter.style.borderRadius = "8px";
        statusFilter.style.background = "#ffffff";
        statusFilter.style.fontSize = "14px";

        categoryFilter.insertAdjacentElement("afterend", statusFilter);

        // Filter products
        function applyFilters() {
            const searchText = searchInput.value.toLowerCase().trim();
            const selectedCategory = categoryFilter.value;
            const selectedDemand = statusFilter.value;

            const rows = tableBody.querySelectorAll("tr");
            let visibleRows = 0;

            rows.forEach(function (row) {
                if (row.cells.length < 6) {
                    return;
                }

                const productName =
                    row.cells[0].textContent.toLowerCase().trim();

                const productCategory =
                    row.cells[1].textContent.trim();

                const statusElement = row.querySelector(".status");
                let productDemand = "";

                if (statusElement) {
                    if (statusElement.classList.contains("high")) {
                        productDemand = "high";
                    } else if (statusElement.classList.contains("medium")) {
                        productDemand = "medium";
                    } else if (statusElement.classList.contains("low")) {
                        productDemand = "low";
                    }
                }

                const matchesSearch =
                    productName.includes(searchText);

                const matchesCategory =
                    selectedCategory === "" ||
                    productCategory === selectedCategory;

                const matchesDemand =
                    selectedDemand === "all" ||
                    productDemand === selectedDemand;

                if (matchesSearch && matchesCategory && matchesDemand) {
                    row.style.display = "";
                    visibleRows++;
                } else {
                    row.style.display = "none";
                }
            });

            const noResults = document.getElementById("noResults");

            if (noResults) {
                noResults.hidden = visibleRows !== 0;
            }
        }

        searchInput.addEventListener("input", applyFilters);
        categoryFilter.addEventListener("change", applyFilters);
        statusFilter.addEventListener("change", applyFilters);
    } else {
        console.error("Search/filter HTML elements are missing.");
    }

    // =========================
    // 2. SALES BAR CHART
    // =========================

    const canvas = document.getElementById("salesChart");

    if (canvas) {
        if (typeof Chart === "undefined") {
            console.error(
                "Chart.js did not load. Check your internet connection."
            );
        } else {
            // Read the JSON data added by Flask in index.html
            const dataElement = document.getElementById("sales-data");

            let salesData = { labels: [], units: [] };

            if (dataElement) {
                try {
                    salesData = JSON.parse(dataElement.textContent);
                } catch (error) {
                    console.error("Could not read sales chart data:", error);
                }
            } else if (window.demandLensSales) {
                // Also supports the earlier window.demandLensSales format
                salesData = window.demandLensSales;
            }

            if (salesData.labels && salesData.units) {
                new Chart(canvas, {
                    type: "bar",

                    data: {
                        labels: salesData.labels,

                        datasets: [{
                            label: "Units Sold",
                            data: salesData.units,
                            backgroundColor: "rgba(79, 70, 229, 0.75)",
                            borderColor: "#4f46e5",
                            borderWidth: 1,
                            borderRadius: 7,
                            maxBarThickness: 55
                        }]
                    },

                    options: {
                        responsive: true,
                        maintainAspectRatio: false,

                        plugins: {
                            legend: {
                                display: false
                            },
                            tooltip: {
                                enabled: true
                            }
                        },

                        scales: {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: "Units Sold"
                                },
                                ticks: {
                                    precision: 0
                                }
                            },

                            x: {
                                title: {
                                    display: true,
                                    text: "Products"
                                },
                                grid: {
                                    display: false
                                }
                            }
                        }
                    }
                });
            }
        }
    }

    // =========================
    // 3. SMOOTH NAVIGATION
    // =========================

    document.querySelectorAll('a[href^="#"]').forEach(function (link) {
        link.addEventListener("click", function (event) {
            const target = document.querySelector(
                link.getAttribute("href")
            );

            if (target) {
                event.preventDefault();

                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });
            }
        });
    });
});
