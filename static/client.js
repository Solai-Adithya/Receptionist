const socket = io("http://" + document.domain + ":5000");

socket.on("connect", () => {
    socket.emit("my event", { data: "I'm connected!" });
});

socket.on("message", (text) => {
    console.log(text);
});
