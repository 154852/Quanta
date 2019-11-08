document.body.setAttribute("style", "--windowheight: " + window.innerHeight + "px;")

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
    "func": ["X", "Y", "Z", "H", "R", "SQRTX", "CNOT", "CCNOT", "CSWAP", "M", "ZX", "add", "sub", "mul", "div", "cmp"],
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
    $scope.code = '# Go to the example tab to see what you can do!';
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
    $scope.examples = [{
        "name": "50-50",
        "code": `alloc 2 # Two bits overall
alloc 1Q(0) # One qubit, starting at index 0
alloc 1b(1) # One classical bit, starting at index 1

H 0Q # Apply a hadamard gate to the first qubit

M 0Q, 1b # Observe the first qubit, and store the result in in the first classical bit (memory index 1)`
    }, {
        "name": "Flip",
        "code": `alloc 3 # Three bits overall
alloc 1Q(0) # One qubit, starting at index 0
alloc 2b(1) # Two classical bits, starting at index 1

H 0Q # 50-50 chance of being on

M 0Q, 1b # Observe the first qubit, and store the result in in the first classical bit (memory index 1)

X 0Q # Apply a Pauli-X gate to the first qubit

M 0Q, 2b # Observe the first qubit again, and store the result in in the second classical bit (memory index 2)`
    }, {
        "name": "Simple Entanglement",
        "code": `alloc 4
alloc 2Q(0)
alloc 2b(2)

# Flip the first qubit, try commenting and uncommenting this line
X 0Q

# Don't flip the second qubit, try commenting and uncommenting this line
# X 1Q
CNOT 0Q, 1Q # CNOT only flips the value of the second (target) bit, if the first (control) bit is on

M 0Q, 2b 
M 1Q, 3b`
    }, {
        "name": "The First Bell State",
        "code": `alloc 4
alloc 2Q(0)
alloc 2b(2)

H 0Q
CNOT 0Q, 1Q # This makes either |00> or |11>, the first bell state

M 0Q, 2b 
M 1Q, 3b`
    }, {
        "name": "Triple Hadamard",
        "code": `alloc 4
alloc 3Q(0)
alloc 1b(3)

H 0Q # 50% chance
H 1Q # 50% chance

CCNOT 0Q, 1Q, 2Q  # 25% chancefor 2Q

M 2Q, 3b

# Run this with 100 shots to see the 25% emerge`
    }, {
        "name": "Superdense Coding",
        "code": `alloc 4
alloc 2Q(0)
alloc 2b(2)

# The particles are entangled into the first bell state
H 0Q
CNOT 0Q, 1Q

# 0Q is sent to Alice, 1Q to Bob

# On Alice's end:
# To send |00>, do nothing
# To send |01>
X 0Q
# To send |10>
#Z 0Q
# To send |11>
#ZX 0Q

# 0Q is sent to Bob, who now has both 0Q and 1Q, where he reads the data
CNOT 0Q, 1Q
H 0Q

M 0Q, 2b
M 1Q, 3b`
    }];

    const textarea = document.querySelector("#instructions textarea");
    const renderedCodeArea = document.querySelector("#instructions code");
    const linenumbers = document.querySelector("#line-numbers");
    const consoleInput = document.querySelector("#console-input input");
    const consoleOutput = document.querySelector("#console-responses");
    const consoleEl = consoleOutput.parentElement;
    const toolsResize = document.querySelector("#tools-resize");
    const toolsDraw = document.querySelector("#tools");
    const controls = document.querySelector("#output-controlls");

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
        controls.classList.add("disabled");

        $http.post("/api/execute", {instructions: $scope.code, shots: $scope.shots}).then(function(response) {
            $scope.output.splice(0, 0, {
                type: 0,
                data: response.data.content
            });

            if (!$scope.$$phase) $scope.$apply();
            controls.classList.remove("disabled");
        }, function(response) {
            $scope.output.splice(0, 0, {
                type: 1,
                text: response.data.error[0] + ": " + response.data.error[1]
            });

            if (!$scope.$$phase) $scope.$apply();
            controls.classList.remove("disabled");
        });
    };

    $scope.setNavSelected = function(idx) {
        $scope.navMode = idx;
        document.querySelector(".selected").classList.remove("selected");
        document.querySelectorAll("#tools nav > div")[idx].classList.add("selected");
    };

    $scope.setExample = function(code) {
        $scope.code = code;
        textarea.value = code;
        renderTextarea();
    };

    let currentProgram = [];
    consoleInput.addEventListener("keyup", function(event) {
        if (event.keyCode == 13) {
            $scope.consoleResponses.push({
                text: renderCode($scope.consoleInput),
                type: 3,
                date: getFormattedTime()
            });

            let m = $scope.consoleInput.match(/read ([0-9]+b?)/);
            if (m != null) {
                consoleEl.classList.add("disabled");

                if (!m[1].endsWith("b")) {
                    $scope.consoleResponses.push({
                        text: parseInt(m[1]),
                        type: 0,
                        date: getFormattedTime()
                    });

                    if(!$scope.$$phase) $scope.$apply();
                    consoleOutput.scrollTop = consoleOutput.scrollHeight;
                    consoleEl.classList.remove("disabled");
                } else $http.post("/api/execute", {instructions: currentProgram, shots: 1}).then(function(response) {
                    const data = response.data.content[parseInt(m[1].slice(0, -1))];
                    if (data != null) {
                        $scope.consoleResponses.push({
                            text: data,
                            type: 0,
                            date: getFormattedTime()
                        });
                    } else {
                        $scope.consoleResponses.push({
                            text: `ERR_CANNOT_PARSE_DATA: The address ${m[1]} does not point to a classical bit`,
                            type: 2,
                            date: getFormattedTime()
                        });
                    }

                    if (!$scope.$$phase) $scope.$apply();
                    consoleOutput.scrollTop = consoleOutput.scrollHeight;
                    consoleEl.classList.remove("disabled");
                }, function(response) {
                    $scope.consoleResponses.push({
                        text: response.data.error[0] + ": " + response.data.error[1],
                        type: 2,
                        date: getFormattedTime()
                    });

                    if(!$scope.$$phase) $scope.$apply();
                    consoleOutput.scrollTop = consoleOutput.scrollHeight;
                    consoleEl.classList.remove("disabled");
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

setInterval(function() {
    if (!document.hasFocus()) window.scrollTo(0, 0)
}, 100);