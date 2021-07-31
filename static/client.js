const socket = io("http://" + document.domain + ":5000");

// socket.on("to-join", (data) => {
//     alert(data);
// });

socket.on("connect", (data) => {
    alert(data);
});
