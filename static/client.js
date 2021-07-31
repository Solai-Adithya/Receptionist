const socket = io("http://" + document.domain + ":5000");

socket.on("joined", (data) => {
    alert(data);
});

socket.on("join", (data) => {
    alert(data);
});
