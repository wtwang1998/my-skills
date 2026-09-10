(() => {
  const VERSION = "v5";

  if (window.__CHATGPT_ROUTE_CHECKER_V5__) {
    console.log(`ChatGPT Route Checker ${VERSION} 已在运行`);
    return;
  }

  window.__CHATGPT_ROUTE_CHECKER_V5__ = true;

  const nativeFetch = window.fetch.bind(window);

  const NativeXHR = window.XMLHttpRequest;
  const nativeXHROpen = NativeXHR.prototype.open;
  const nativeXHRSend = NativeXHR.prototype.send;

  const nativeBeacon = navigator.sendBeacon
    ? navigator.sendBeacon.bind(navigator)
    : null;

  const state = {
    active: false,

    turnKey: null,

    requestModel: null,
    thinkingEffort: null,

    serverModel: null,
    assistantModel: null,
    resolvedModel: null,

    requestedExperience: null,
    domModel: null,

    startedAt: null
  };

  const oldPanel = document.getElementById(
    "__chatgpt_route_checker_panel__"
  );

  if (oldPanel) oldPanel.remove();

  const panel = document.createElement("div");

  panel.id = "__chatgpt_route_checker_panel__";

  Object.assign(panel.style, {
    position: "fixed",
    right: "16px",
    bottom: "16px",
    zIndex: "2147483647",

    width: "410px",
    maxWidth: "calc(100vw - 32px)",

    padding: "14px 16px",

    border: "1px solid #444",
    borderRadius: "12px",

    background: "#111",
    color: "#eee",

    font:
      "13px/1.7 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace",

    boxShadow: "0 8px 30px rgba(0,0,0,.4)"
  });

  document.documentElement.appendChild(panel);

  function esc(value) {
    return String(value).replace(
      /[&<>"']/g,
      c =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;"
        })[c]
    );
  }

  function pending(value) {
    return value
      ? esc(value)
      : '<span style="color:#999">搜索中…</span>';
  }

  function refreshDomModel() {
    const nodes = document.querySelectorAll(
      '[data-message-author-role="assistant"]'
    );

    if (!nodes.length) return;

    const slug =
      nodes[nodes.length - 1].getAttribute(
        "data-message-model-slug"
      );

    if (slug) {
      state.domModel = slug;
    }
  }

  function modelFamily(slug) {
    const match = String(slug || "").match(
      /^gpt-(\d+)-(\d+)/i
    );

    return match
      ? `gpt-${match[1]}-${match[2]}`
      : null;
  }

  function verdict() {
    if (!state.active) {
      return "⏳ 等待发送一条新消息";
    }

    if (!state.requestModel) {
      return "🔎 正在读取请求信息…";
    }

    if (!state.serverModel) {
      return "🧠 正在等待服务端模型标注…";
    }

    if (
      state.requestModel ===
      state.serverModel
    ) {
      return "✅ 请求模型与服务端模型标注一致";
    }

    const reqFamily =
      modelFamily(state.requestModel);

    const serverFamily =
      modelFamily(state.serverModel);

    if (
      reqFamily &&
      serverFamily &&
      reqFamily === serverFamily
    ) {
      return "✅ 同一模型系列（内部 slug 不同）";
    }

    return "🚨 请求模型与服务端模型标注不一致";
  }

  function render() {
    refreshDomModel();

    panel.innerHTML = `
      <div style="
        font-weight:700;
        font-size:14px;
        margin-bottom:8px
      ">
        ChatGPT Route Checker ${VERSION}
      </div>

      <div style="margin-bottom:10px">
        ${verdict()}
      </div>

      <div style="
        border-top:1px solid #333;
        border-bottom:1px solid #333;
        padding:10px 0;
        margin-bottom:10px
      ">
        <div style="color:#aaa">
          服务端回复模型标注
        </div>

        <div style="
          font-size:18px;
          font-weight:700;
          margin-top:2px
        ">
          ${pending(state.serverModel)}
        </div>

        <div style="
          color:#777;
          font-size:11px;
          margin-top:2px
        ">
          server_ste_metadata.model_slug
        </div>
      </div>

      <div>
        request.model：
        <b>${pending(state.requestModel)}</b>

        <br>

        request.thinking_effort：
        <b>${pending(state.thinkingEffort)}</b>

        <br><br>

        server_ste_metadata.model_slug：
        <b>${pending(state.serverModel)}</b>

        <br>

        assistant metadata.model_slug：
        <b>${pending(state.assistantModel)}</b>

        <br>

        resolved_model_slug：
        <b>${pending(state.resolvedModel)}</b>

        <br>

        requested_model_experience：
        <b>${pending(state.requestedExperience)}</b>

        <br>

        DOM data-message-model-slug：
        <b>${pending(state.domModel)}</b>
      </div>

      <div style="
        border-top:1px solid #333;
        margin-top:10px;
        padding-top:7px;
        color:#777;
        font-size:11px
      ">
        主判断：server_ste_metadata.model_slug
      </div>
    `;
  }


  function extractTurnKey(req) {
    try {
      const messages =
        Array.isArray(req?.messages)
          ? req.messages
          : [];

      // 从后往前找最新 user message
      for (
        let i = messages.length - 1;
        i >= 0;
        i--
      ) {
        const msg = messages[i];

        if (
          msg?.author?.role === "user" &&
          msg?.id
        ) {
          return msg.id;
        }
      }

      // 某些请求结构可能不同
      if (req?.message?.author?.role === "user") {
        return req.message.id || null;
      }
    } catch {}

    return null;
  }

  function beginOrUpdateTurn(req) {
    const newTurnKey =
      extractTurnKey(req);

    const isDefinitelyNewTurn =
      newTurnKey &&
      newTurnKey !== state.turnKey;

    if (!state.active) {
      state.active = true;
      state.turnKey =
        newTurnKey || `turn-${Date.now()}`;

      state.startedAt = Date.now();

      state.serverModel = null;
      state.assistantModel = null;
      state.resolvedModel = null;
      state.requestedExperience = null;
      state.domModel = null;
    }

    else if (isDefinitelyNewTurn) {
      state.turnKey = newTurnKey;
      state.startedAt = Date.now();

      state.serverModel = null;
      state.assistantModel = null;
      state.resolvedModel = null;
      state.requestedExperience = null;
      state.domModel = null;
    }

    if (typeof req?.model === "string") {
      state.requestModel =
        req.model;
    }

    if (
      typeof req?.thinking_effort ===
      "string"
    ) {
      state.thinkingEffort =
        req.thinking_effort;
    }

    render();
  }


  function applyServerMetadata(meta) {
    if (
      !meta ||
      typeof meta !== "object"
    ) {
      return;
    }

    if (
      typeof meta.model_slug ===
      "string"
    ) {
      state.serverModel =
        meta.model_slug;
    }

    if (
      typeof meta.requested_model_experience ===
      "string"
    ) {
      state.requestedExperience =
        meta.requested_model_experience;
    }

    render();
  }

  function scanObject(
    obj,
    depth = 0,
    seen = new WeakSet()
  ) {
    if (
      obj == null ||
      depth > 16
    ) {
      return;
    }

    if (typeof obj === "string") {
      const text = obj.trim();

      if (
        (
          text.startsWith("{") ||
          text.startsWith("[")
        ) &&
        (
          text.includes("model_slug") ||
          text.includes(
            "server_ste_metadata"
          ) ||
          text.includes(
            "resolved_model_slug"
          )
        )
      ) {
        try {
          scanObject(
            JSON.parse(text),
            depth + 1,
            seen
          );
        } catch {}
      }

      return;
    }

    if (typeof obj !== "object") {
      return;
    }

    if (seen.has(obj)) {
      return;
    }

    seen.add(obj);


    if (
      obj.type ===
        "server_ste_metadata" &&
      obj.metadata
    ) {
      applyServerMetadata(
        obj.metadata
      );
    }


    if (
      obj.server_ste_metadata &&
      typeof obj.server_ste_metadata ===
        "object"
    ) {
      applyServerMetadata(
        obj.server_ste_metadata
      );
    }

    if (
      obj.turn_analytics
        ?.server_ste_metadata
    ) {
      applyServerMetadata(
        obj.turn_analytics
          .server_ste_metadata
      );
    }


    if (
      obj.author?.role ===
        "assistant" &&
      typeof obj.metadata?.model_slug ===
        "string"
    ) {
      state.assistantModel =
        obj.metadata.model_slug;

      render();
    }

    if (
      obj.message?.author?.role ===
        "assistant" &&
      typeof obj.message?.metadata?.model_slug ===
        "string"
    ) {
      state.assistantModel =
        obj.message.metadata.model_slug;

      render();
    }


    if (
      typeof obj.resolved_model_slug ===
      "string"
    ) {
      state.resolvedModel =
        obj.resolved_model_slug;

      render();
    }

    for (
      const value of Object.values(obj)
    ) {
      scanObject(
        value,
        depth + 1,
        seen
      );
    }
  }

  function parseJSONCandidate(text) {
    if (!text) return;

    const value = text.trim();

    if (
      !value ||
      value === "[DONE]"
    ) {
      return;
    }

    try {
      scanObject(
        JSON.parse(value)
      );
    } catch {}
  }


  async function watchStream(response) {
    if (!response?.body) {
      try {
        scanWholeText(
          await response.text()
        );
      } catch {}

      return;
    }

    const reader =
      response.body.getReader();

    const decoder =
      new TextDecoder();

    let buffer = "";
    let eventData = [];

    try {
      while (true) {
        const {
          value,
          done
        } = await reader.read();

        if (done) break;

        buffer += decoder.decode(
          value,
          {
            stream: true
          }
        );

        let newlineIndex;

        while (
          (
            newlineIndex =
              buffer.indexOf("\n")
          ) !== -1
        ) {
          let line =
            buffer.slice(
              0,
              newlineIndex
            );

          buffer =
            buffer.slice(
              newlineIndex + 1
            );

          if (
            line.endsWith("\r")
          ) {
            line =
              line.slice(0, -1);
          }

          // SSE 空行：
          // 一个 event 结束
          if (line === "") {
            if (
              eventData.length
            ) {
              parseJSONCandidate(
                eventData.join("\n")
              );

              eventData = [];
            }

            continue;
          }

          if (
            line.startsWith("data:")
          ) {
            eventData.push(
              line
                .slice(5)
                .trimStart()
            );

            continue;
          }

          const trimmed =
            line.trim();

          if (
            trimmed.startsWith("{") ||
            trimmed.startsWith("[")
          ) {
            parseJSONCandidate(
              trimmed
            );
          }
        }
      }

      buffer += decoder.decode();

      if (buffer.trim()) {
        const rest =
          buffer.trim();

        if (
          rest.startsWith("data:")
        ) {
          eventData.push(
            rest
              .slice(5)
              .trimStart()
          );
        } else {
          parseJSONCandidate(
            rest
          );
        }
      }

      if (eventData.length) {
        parseJSONCandidate(
          eventData.join("\n")
        );
      }
    } catch (err) {
      console.debug(
        "[Route Checker] stream:",
        err
      );
    }


  }

  function scanWholeText(text) {
    if (
      !text ||
      typeof text !== "string"
    ) {
      return;
    }

    // 整体 JSON
    try {
      scanObject(
        JSON.parse(text)
      );
    } catch {}

    // SSE / NDJSON
    for (
      let line of
        text.split(/\r?\n/)
    ) {
      line = line.trim();

      if (!line) continue;

      if (
        line.startsWith("data:")
      ) {
        line =
          line.slice(5).trim();
      }

      parseJSONCandidate(line);
    }
  }


  async function bodyToText(body) {
    try {
      if (body == null) {
        return "";
      }

      if (
        typeof body ===
        "string"
      ) {
        return body;
      }

      if (
        body instanceof Blob
      ) {
        return await body.text();
      }

      if (
        body instanceof
          URLSearchParams
      ) {
        return body.toString();
      }

      if (
        body instanceof
          ArrayBuffer
      ) {
        return new TextDecoder()
          .decode(body);
      }

      if (
        ArrayBuffer.isView(body)
      ) {
        return new TextDecoder()
          .decode(body);
      }
    } catch {}

    return "";
  }

  async function getRequestText(
    input,
    init
  ) {
    if (init?.body != null) {
      return await bodyToText(
        init.body
      );
    }

    if (
      input instanceof Request
    ) {
      try {
        return await input
          .clone()
          .text();
      } catch {}
    }

    return "";
  }

  function isConversation(
    url,
    method
  ) {
    return (
      method === "POST" &&
      /\/backend-api\/f\/conversation(?:\?|$)/
        .test(url)
    );
  }

  function isTelemetry(
    url,
    method
  ) {
    return (
      method === "POST" &&
      /\/ces\/v1\/telemetry\/intake(?:\?|$)/
        .test(url)
    );
  }



  window.fetch =
    async function(
      input,
      init = {}
    ) {
      const url =
        typeof input ===
        "string"
          ? input
          : input?.url || "";

      const method =
        String(
          init.method ||
          input?.method ||
          "GET"
        ).toUpperCase();

      let reqText = "";

      if (
        isConversation(
          url,
          method
        ) ||
        isTelemetry(
          url,
          method
        )
      ) {
        reqText =
          await getRequestText(
            input,
            init
          );
      }

      if (
        isConversation(
          url,
          method
        )
      ) {
        try {
          beginOrUpdateTurn(
            JSON.parse(reqText)
          );
        } catch {}
      }


      if (
        isTelemetry(
          url,
          method
        )
      ) {
        scanWholeText(reqText);
      }

      const response =
        await nativeFetch(
          input,
          init
        );

      if (
        isConversation(
          url,
          method
        )
      ) {
        try {
          // clone，不影响网页自身读取
          watchStream(
            response.clone()
          );
        } catch {}
      }

      return response;
    };


  NativeXHR.prototype.open =
    function(
      method,
      url,
      ...rest
    ) {
      this.__routeCheckerMethod =
        String(
          method || "GET"
        ).toUpperCase();

      this.__routeCheckerUrl =
        String(url || "");

      return nativeXHROpen.call(
        this,
        method,
        url,
        ...rest
      );
    };

  NativeXHR.prototype.send =
    function(body) {
      const url =
        this.__routeCheckerUrl || "";

      const method =
        this.__routeCheckerMethod ||
        "GET";

      bodyToText(body).then(
        text => {
          if (
            isConversation(
              url,
              method
            )
          ) {
            try {
              beginOrUpdateTurn(
                JSON.parse(text)
              );
            } catch {}
          }

          if (
            isTelemetry(
              url,
              method
            )
          ) {
            scanWholeText(text);
          }
        }
      );

      if (
        isConversation(
          url,
          method
        )
      ) {
        this.addEventListener(
          "loadend",
          () => {
            try {
              if (
                !this.responseType ||
                this.responseType ===
                  "text"
              ) {
                scanWholeText(
                  this.responseText
                );
              }
            } catch {}
          },
          {
            once: true
          }
        );
      }

      return nativeXHRSend.call(
        this,
        body
      );
    };


  if (nativeBeacon) {
    try {
      navigator.sendBeacon =
        function(
          url,
          data
        ) {
          const target =
            String(url || "");

          if (
            /\/ces\/v1\/telemetry\/intake(?:\?|$)/
              .test(target)
          ) {
            bodyToText(data).then(
              scanWholeText
            );
          }

          return nativeBeacon(
            url,
            data
          );
        };
    } catch {}
  }


  const observer =
    new MutationObserver(() => {
      const old =
        state.domModel;

      refreshDomModel();

      if (
        old !== state.domModel
      ) {
        render();
      }
    });

  observer.observe(
    document.body,
    {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: [
        "data-message-model-slug"
      ]
    }
  );

  // ============================================================

  render();

  window.__CHATGPT_ROUTE_CHECK_STATE__ =
    state;

  console.log(
    `ChatGPT Route Checker ${VERSION} 已启动`
  );
})();