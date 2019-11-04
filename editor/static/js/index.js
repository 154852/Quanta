document.body.setAttribute("style", "--windowheight: " + window.innerHeight + "px;")
// const iOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;

const app = angular.module("quantum", ["ngSanitize"]);

function getFormattedTime() {
    const date = new Date();

    const twoChar = function(v) {
        return (v < 10? "0":"") + v.toString()
    }

    return `${twoChar(date.getHours())}:${twoChar(date.getMinutes())}:${twoChar(date.getSeconds())}.${date.getMilliseconds()}`;
}

const codeSyntax = {
    "keyword": ["alloc", "read", "mov", "jmp", "jgt", "jlt", "je", "jne", "jle", "jge"],
    "func": ["X", "Y", "Z", "H", "R", "SQRTX", "CNOT", "CCNOT", "CSWAP", "M", "add", "sub", "mul", "div", "cmp"],
    "number": [/([0-9.]+)/g],
    "address": [/([0-9]+(Q|b))/g, /(\.[a-z0-9A-Z_]+:)/g, /^j[a-z][a-z]? (\.[a-z0-9A-Z_]+)/gm],
    "comment": [/^.*(#.*)$/gm]
};

function renderCode(string) {
    string = "\n " + string.replace("<", "&lt;").replace(">", "&gt;") + " \n";

    let found = [];
    for (const key in codeSyntax) {
        for (const pattern of codeSyntax[key]) {
            if (typeof pattern == "string") {
                const regex = new RegExp("\\s+" + pattern + "\\s+", "g");
                let m;
                do {
                    m = regex.exec(string);
                    if (m) {
                        let idx = m.index + 1, end = m.index + m[0].length - 1;
                        found = found.filter((f) => !(f.start >= idx && f.start <= end));
                        found.push({start: idx, end: end, type: key})
                    }
                } while (m != null);
            } else {
                let m;
                do {
                    m = pattern.exec(string);
                    if (m) {
                        let idx = m.index + m[0].indexOf(m[1]), end = m.index + m[0].indexOf(m[1]) + m[1].length;
                        found = found.filter((f) => !(f.start >= idx && f.start <= end));
                        found.push({start: idx, end: end, type: key})
                    }
                } while (m != null);
            }
        }
    }

    found.sort((a, b) => b.start - a.start);
    
    for (const f of found) {
        string = string.slice(0, f.start) + `<span class="${f.type}">` + string.slice(f.start, f.end) + "</span>" + string.slice(f.end);
    }

    return string.slice(1, -1).replace(/\n/g, "<br />");
}

app.controller("main-controller", function($scope, $http) {
    $scope.code = `\
alloc 4
alloc 3Q(0)
alloc 1b(3)

# Initialise two qubits
H 0Q
H 1Q

CCNOT 0Q, 1Q, 2Q

M 2Q, 3b`;
    $scope.navMode = 0;
    $scope.shots = 1;
    $scope.output = [];
    $scope.consoleInput = "";
    $scope.consoleResponses = [
        {
            text: "Start the console by allocating memory with `alloc`. Later, to read memory type `read <idx>b`.",
            type: 1,
            date: getFormattedTime()
        }
    ];

    const textarea = document.querySelector("#instructions textarea");
    const renderedCodeArea = document.querySelector("#instructions code");
    const linenumbers = document.querySelector("#line-numbers");
    const consoleInput = document.querySelector("#console-input input");
    const consoleOutput = document.querySelector("#console-responses");
    const toolsResize = document.querySelector("#tools-resize");
    const toolsDraw = document.querySelector("#tools");

    let heldTools = false;
    toolsResize.addEventListener("mousedown", () => {heldTools = true;});
    toolsResize.addEventListener("touchstart", (event) => {
        heldTools = true;
    });
    window.addEventListener("mouseup", () => {heldTools = false;});
    toolsResize.addEventListener("touchend", () => {heldTools = false;});
    window.addEventListener("mousemove", function(event) {
        if (heldTools) {
            toolsDraw.setAttribute("style", "--toolsheight: " + Math.max((window.innerHeight - event.clientY), 34) + "px;");
        }
    });
    window.addEventListener("touchmove", function(event) {
        if (heldTools) {
            toolsDraw.setAttribute("style", "--toolsheight: " + Math.max((window.innerHeight - event.touches[0].clientY), 34) + "px;");
        }
    });

    renderedCodeArea.innerHTML = renderCode($scope.code);
    const renderTextarea = function(event) {
        $scope.code = textarea.value;

        const lineCount = $scope.code.split(/\r|\r\n|\n/).length;
        let html = "";
        for (let i = 0; i < lineCount; i++) {
            html += (i + 1) + "<br/>";
        }
        linenumbers.innerHTML = html;

        textarea.style.height = textarea.scrollHeight + "px";
        renderedCodeArea.innerHTML = renderCode($scope.code);
    }

    textarea.addEventListener("input", renderTextarea);

    $scope.run = function() {
        $http.post("/api/execute", {instructions: $scope.code, shots: $scope.shots}).then(function(response) {
            $scope.output.splice(0, 0, {
                type: 0,
                data: response.data.content
            });

            if (!$scope.$$phase) $scope.$apply();
        }, function(response) {
            $scope.output.splice(0, 0, {
                type: 1,
                text: response.data.error[0] + ": " + response.data.error[1]
            });

            if (!$scope.$$phase) $scope.$apply();
        });
    };

    $scope.setNavSelected = function(idx) {
        $scope.navMode = idx;
        document.querySelector(".selected").classList.remove("selected");
        document.querySelectorAll("#tools nav > div")[idx].classList.add("selected");
    };

    let currentProgram = [];
    consoleInput.addEventListener("keyup", function(event) {
        if (event.keyCode == 13) {
            $scope.consoleResponses.push({
                text: renderCode($scope.consoleInput),
                type: 3,
                date: getFormattedTime()
            });

            let m = $scope.consoleInput.match(/read ([0-9]+)b/);
            if (m != null) {
                $http.post("/api/execute", {instructions: currentProgram, shots: 1}).then(function(response) {
                    $scope.consoleResponses.push({
                        text: response.data.content[parseInt(m[1])],
                        type: 0,
                        date: getFormattedTime()
                    });

                    if(!$scope.$$phase) {
                        $scope.$apply();
                    }

                    consoleOutput.scrollTop = consoleOutput.scrollHeight;
                }, function(response) {
                    $scope.consoleResponses.push({
                        text: response.data.error[0] + ": " + response.data.error[1],
                        type: 2,
                        date: getFormattedTime()
                    });

                    if(!$scope.$$phase) {
                        $scope.$apply();
                    }

                    consoleOutput.scrollTop = consoleOutput.scrollHeight;
                });
            } else if ($scope.consoleInput == "reset") {
                currentProgram  = [];
                $scope.consoleResponses.push({
                    text: "Start the console by allocating memory with `alloc`. Later, to read memory type `read`.",
                    type: 1,
                    date: getFormattedTime()
                });
            } else if ($scope.consoleInput == "clear") {
                $scope.consoleResponses = [];
            } else currentProgram.push($scope.consoleInput);

            $scope.consoleInput = "";
            $scope.$apply();

            setTimeout(() => {consoleOutput.scrollTop = consoleOutput.scrollHeight;}, 20)
        }
    })
});

document.querySelectorAll("textarea,input").forEach((e) => {
    e.addEventListener("blur", () => {window.scrollTo(0, 0)});
    e.addEventListener("focus", () => {window.scrollTo(0, 0)});
});