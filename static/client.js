const socket = io("http://" + document.domain + ":5000");

socket.on("connect", (data) => {
    console.log(data);
});

const l = String(window.location);
const found = l.match(/.*\/(join|manage)\/(\w+).*/);
console.log(found);
const m = found[1];
const r = found[2];

if (m === "join") {
    setInterval(() => {
        fetch("/get_QP", {
            method: "POST",
            dataType: "json",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ roomID: r }),
        })
            .then((res) => res.json())
            .then((res) => {
                // console.log(res);
                const e = document.getElementById("queuePosition");
                if (m === "join" && res["queuePosition"] !== e.innerText) {
                    e.innerText = res["queuePosition"];
                }
            });
    }, 2000);
}

// BOILERPLATE
function notifyMe(user, message) {
    // Let's check if the browser supports notifications
    if (!("Notification" in window)) {
        alert("This browser does not support desktop notification");
    }
    // Let's check if the user is okay to get some notification
    else if (Notification.permission === "granted") {
        // If it's okay let's create a notification
        var options = {
            body: message,
        };
        var notification = new Notification(
            user + " Posted a comment",
            options
        );
    }
    // Otherwise, we need to ask the user for permission
    // Note, Chrome does not implement the permission static property
    // So we have to check for NOT 'denied' instead of 'default'
    else if (Notification.permission !== "denied") {
        Notification.requestPermission(function (permission) {
            // Whatever the user answers, we make sure we store the information
            if (!("permission" in Notification)) {
                Notification.permission = permission;
            }
            // If the user is okay, let's create a notification
            if (permission === "granted") {
                var options = {
                    body: message,
                    dir: "ltr",
                };
                var notification = new Notification(
                    user + " Posted a comment",
                    options
                );
            }
        });
    }
}

// At last, if the user already denied any notification, and you
// want to be respectful there is no need to bother them any more.
