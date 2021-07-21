const socket = io("http://" + document.domain + "5000");

socket.on("message", (text) => {
    console.log(text);
});
