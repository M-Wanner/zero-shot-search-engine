const currentHost = window.location.hostname;
const BASE_API_URL = `http://${currentHost}:8000/api`;

const searchInput = document.getElementById("searchInput");
const imageInput = document.getElementById("imageInput");
const searchBtn = document.getElementById("searchBtn");
const resultsContainer = document.getElementById("results");
const loader = document.getElementById("loader");


const imagePreviewContainer = document.getElementById("imagePreviewContainer");
const imagePreview = document.getElementById("imagePreview");
const fileNameDisplay = document.getElementById("fileNameDisplay");
const removeImgBtn = document.getElementById("removeImgBtn");


const modal = document.getElementById("imageModal");
const modalImage = document.getElementById("modalImage");
const modalCaption = document.getElementById("modalCaption");
const modalClose = document.getElementById("modalClose");


imageInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(evt) {
            imagePreview.src = evt.target.result;
            fileNameDisplay.textContent = file.name;
            imagePreviewContainer.classList.remove("hidden");
        };
        reader.readAsDataURL(file);
        searchInput.value = "";
    }
});


function clearImageSelection() {
    imageInput.value = "";
    imagePreview.src = "";
    fileNameDisplay.textContent = "";
    imagePreviewContainer.classList.add("hidden");
}

removeImgBtn.addEventListener("click", clearImageSelection);


async function performSearch() {
    const query = searchInput.value.trim();
    const imageFile = imageInput.files[0];

    if (!query && !imageFile) return;

    loader.classList.remove("hidden");
    resultsContainer.innerHTML = "";

    try {
        let response;
        if (imageFile) {

            const formData = new FormData();
            formData.append("file", imageFile);
            
            response = await fetch(`${BASE_API_URL}/search-by-image?top_k=9`, {
                method: "POST",
                body: formData
            });
        } else {
            response = await fetch(`${BASE_API_URL}/search?q=${encodeURIComponent(query)}&top_k=9`);
        }

        if (!response.ok){
            throw new Error("Search request failed");
        }
        
        const data = await response.json();
        renderResults(data.results);
    } catch (error) {
        console.error(error);
        resultsContainer.innerHTML = "Error executing search.";
    } finally {
        loader.classList.add("hidden");
    }
}


function renderResults(results) {
    if (results.length === 0) {
        resultsContainer.innerHTML = "<p>No matching images found.</p>";
        return;
    }

    results.forEach(item => {
        const card = document.createElement("div");
        card.className = "card";
        
        card.innerHTML = `
            <img src="${item.url}" alt="${item.filename}" loading="lazy">
            <div class="card-body">
                <span style="font-size:0.85rem; color:#777;">${item.filename}</span>
                <span class="score-tag">Score: ${(item.score * 100).toFixed(1)}%</span>
            </div>
        `;

        card.addEventListener("click", () => {
            modalImage.src = item.url;
            modalCaption.textContent = `${item.filename} (Similarity Score: ${(item.score * 100).toFixed(1)}%)`;
            modal.classList.remove("hidden");
        });

        resultsContainer.appendChild(card);
    });
}

modalClose.addEventListener("click", () => modal.classList.add("hidden"));
modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.add("hidden");
});

searchBtn.addEventListener("click", performSearch);
searchInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") performSearch();
});