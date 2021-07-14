const socket = io("http://127.0.0.1:8080");

socket.on("message", (text) => {
    console.log(text);
});
