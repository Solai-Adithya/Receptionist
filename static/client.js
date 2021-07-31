const socket = io("http://" + document.domain + ":5000");
participantRoomNameSpace = io("/p_room");

participantRoomNameSpace.on("joined", (data) => {
    alert(data);
});

participantRoomNameSpace.on("join", (data) => {
    alert(data);
});
