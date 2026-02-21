// Upload Video to backend (MinIO storage)
export async function uploadVideo(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch("http://localhost:8000/upload", {
    method: "POST",
    body: formData
  });

  if (!res.ok) {
    throw new Error("Upload failed");
  }

  return res.json(); 
  // expected:
  // {
  //   file_id: "...",
  //   signed_url: "..."
  // }
}


// Analyse video
export async function analyseVideo(file_id) {
  const res = await fetch("http://localhost:8000/analyse", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ file_id })
  });

  if (!res.ok) {
    throw new Error("Analysis failed");
  }

  return res.json();
}


// Convert videos
export async function convertVideos(payload) {
  const res = await fetch("http://localhost:8000/convert", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    throw new Error("Conversion failed");
  }

  return res.json();
}