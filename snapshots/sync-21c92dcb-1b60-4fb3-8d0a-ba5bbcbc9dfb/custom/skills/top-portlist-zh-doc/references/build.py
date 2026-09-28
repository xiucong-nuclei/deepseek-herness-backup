# -*- coding: utf-8 -*-
import re, csv
from collections import Counter

SRC = "/home/ubuntu/riscv_docs/.dsh-uploads/session-998f1e3f-0ae6-4f31-b5ff-44e399bbaebd/f36c2236e9b9cffd-pd_subsys_top_ports.csv"
OUT = "/home/ubuntu/riscv_docs/pd_subsys_top_ports_zh.md"

rows = []
with open(SRC, encoding="utf-8") as f:
    rd = csv.DictReader(f)
    for i, r in enumerate(rd, start=2):
        rows.append((r["name"].strip(), r["width"].strip(), r["direction"].strip().lower(), i))

DIR = {"input": "输入", "output": "输出"}
GEN = 1
EXACT = {}
by_name = {}

def ex(*pairs):
    for n, d, g in pairs:
        EXACT[n] = (d, g)

# ============================= CPU / core =============================
ex(
    ("core0_dmi2tap_clk_ack", "DMI 响应有效信号：指示外部 TAP(DTM) 发起的 DMI 访问已完成，与 tap2dmi_tck_req 构成请求/响应握手（InSight §9.2）", 0),
    ("core0_dmi2tap_rdata", "DMI 响应数据（读回数据）。注：InSight 文档中 dmi2tap_rdata 为 41 位（含地址），本设计按 32 位读数据引出", 0),
    ("core0_dtm_dmi_resetn", "DMI 复位信号，低有效：复位核内 Debug Module 的 DMI 接口（InSight §9.2）", 0),
    ("core0_tap2dmi_data", "DMI 请求数据（41 位，含地址/控制信息），由外部 TAP(DTM) 在 DMI 访问时驱动（InSight §9.2）", 0),
    ("core0_tap2dmi_tck_req", "DMI 请求有效信号：高电平表示外部 TAP(DTM) 发出一次 DMI 访问请求（InSight §9.2）", 0),
    ("core0_dbg_no_sleep", "调试睡眠控制：0=睡眠，1=不睡眠。核进入深睡时若 override_dm_sleep=1 则输出 1，否则输出 0；为 0 时外部 TAP(DTM) 不应再发送 DMI 请求（InSight §9.2）", 0),
    ("core0_i_dbg_stop", "调试功能禁用：1=禁用，调试器不能再通过 JTAG 接口调试该核（不能访问 DM 寄存器）；0=不禁用（InSight §9.3）", 0),
    ("cpu_dbg_stop_at_boot", "dbg_stop_at_boot：1=禁止调试器操作 CPU（只能访问 DM 寄存器，不能运行/控制 CPU）；0=允许（InSight §9.3）", 0),
    ("core0_override_dm_sleep", "覆盖 DM 睡眠状态：1=核进入深睡时调试器仍可访问 DM 寄存器；0=不覆盖，深睡时不可访问（InSight §9.3）", 0),
    ("core0_dbg_stoptime", "指示外部定时器应停止计数（由 DCSR.stoptime 位控制）：1=调试模式下停止计时，可用于停止 SoC 定时器（InSight §9.3）", 0),
    ("core0_mtime_toggle_a", "周期脉冲信号（通常为 SoC 系统节拍，建议由慢速时钟如 rtc_clk 驱动寄存器输出），驱动核内部 TIMER(mtime) 计数器自增；核内先同步再双边沿采样（300 Product §6.15）", 0),
    ("core0_icache_disable_init", "置 1 时跳过 I-Cache Tag RAM 的上电初始化（复位后立即可用，软件稍后可做 INVAL），缩短上电流程；仅当核配置 I-Cache 时存在（300 Product §5.12）", 0),
    ("core0_hart_id", "HART ID 指示信号：范围 0~1023，其值反映到 CSR mhartid；单核建议接 0（300 Product §6.15）", 0),
    ("core0_reset_vector", "复位后取指的第一条指令 PC 值：SoC 级可用其控制核复位后的起始执行地址（300 Product §6.15）", 0),
    ("core0_core_wfi_mode", "=1 表示核已进入睡眠模式（浅睡或深睡），可用于门控核时钟等低功耗控制（300 Product §6.15）", 0),
    ("core0_core_sleep", "核睡眠深度指示（core_sleep_value）：当 core_wfi_mode=1 时，1=深睡、0=浅睡，供 SoC 决定是否关闭相关时钟/电源（300 Product §6.15）", 0),
    ("soc_clk_core0_stop_on_reset", "core0 复位后停止信号（stop_on_reset）：复位后停住核，允许其它主机（如 DMA）经从口预加载 ILM/DLM；仅复位后一次有效，运行中不能停核（300 Product §6.15；前缀 soc_clk 为时钟域名）", 0),
    ("core1_sysrstreq", "处理器核（core1）的系统复位请求输出：由 JTAG 与软复位请求产生；SoC 可用它触发该核的 core_reset_n（复位除 JTAG 外逻辑），不应触发 por 复位，建议 SoC 侧延迟一拍（300 Product §6.15 sysrstreq）", 0),
    ("cpu1_cpu_clk", "CPU1 的处理器主功能时钟输入（cpu_clk 时钟域），由 SoC 时钟源提供（生成）", 1),
    ("cpu0_cpu_clk_en", "CPU0 处理器时钟使能（高有效）：由 SoC 时钟/低功耗管理控制，用于门控 CPU0 的 cpu 功能时钟（生成）", 1),
    ("sync_cpu0_cpu_clk_core0_por_reset_n", "core0 的上电复位（por_reset_n，低有效，复位整个核含 JTAG 逻辑），在 cpu0_cpu_clk 域内经同步（异步置位/同步释放）后输入（300/NA300 por_reset_n；同步由集成实现）", 0),
    ("sync_cpu0_cpu_clk_core0_core_reset_n", "core0 的系统复位（core_reset_n，低有效，复位核除 JTAG 外逻辑），在 cpu0_cpu_clk 域内经同步后输入（300/NA300 core_reset_n；同步由集成实现）", 0),
    ("wwdg0_wdogres", "由 WWDG 产生的复位输出（看门狗复位信号），供 SoC 复位控制使用（WWDG 文档 WDOGRES）", 0),
)

# ============================= 模块 cfg 时钟（文档语义） =============================
MOD_CLK_DOC = {
    "usart0": ("USART0 的配置时钟（cfg_clk = 文档 clk：Clock for usart in ICB clock domain，ICB 配置时钟域）", 0),
    "usart1": ("USART1 的配置时钟（cfg_clk = 文档 clk：Clock for usart in ICB clock domain，ICB 配置时钟域）", 0),
    "qspi_xip0": ("QSPI_XIP0 的时钟（cfg_clk = 文档 clk：Clock for spi），驱动 SPI 逻辑", 0),
    "qspi1": ("QSPI1 的时钟（cfg_clk = 文档 clk：Clock for spi），驱动 SPI 逻辑", 0),
    "qspi2": ("QSPI2 的时钟（cfg_clk = 文档 clk：Clock for spi），驱动 SPI 逻辑", 0),
    "lgpio0": ("LGPIO0 的配置时钟（cfg_clk = 文档 clk：Clock for LGPIO in ICB clock domain）", 0),
    "sai0": ("SAI0 的配置时钟（cfg_clk = 文档 sys_clk：ICB 配置时钟域时钟）", 0),
    "rtc0": ("RTC0 的配置时钟（cfg_clk = 文档 icb_clk：ICB Bus clock，用于寄存器配置）", 0),
    "udma0": ("uDMA0 的配置时钟（cfg_clk = 文档 clk：Clock signal）", 0),
    "udma1": ("uDMA1 的配置时钟（cfg_clk = 文档 clk：Clock signal）", 0),
    "wwdg0": ("WWDG0 的配置时钟（cfg_clk，ICB 配置域）；WWDG 文档未单列时钟行，按名称拟写（生成）", 1),
}
GEN_CLK_TMPL = "%s 的%s时钟（%s）：由 SoC 时钟源提供，作为 %s 的%s时钟域时钟（生成）"

# ============================= 总线协议信号描述 =============================
ICB_DESC = {
    "cmd_valid": "请求有效：指示主机正在驱动有效的读/写命令（写数据、地址与控制信息在 cmd_ready 拉高前保持稳定）",
    "cmd_ready": "请求就绪：指示从机已准备好接收命令",
    "cmd_sel": "从机/区域选择：指示本次传输访问的目标从机（或从机内目标区域）",
    "cmd_read": "传输方向：1=读传输，0=写传输",
    "cmd_addr": "访问的字节地址（宽度可参数化）",
    "cmd_wdata": "写数据",
    "cmd_wmask": "字节写选通：每字节 1 位，wmask[n]=1 表示写入 wdata 第 n 字节通道",
    "cmd_size": "突发每拍传输大小：每拍字节数 = 2^cmd_size（支持 1/2/4/…/128 字节）",
    "cmd_lock": "锁定访问：指示原子/锁定型传输",
    "cmd_excl": "独占访问：指示独占（LDEX/STEX）型传输",
    "cmd_xlen": "突发长度：突发内数据传输拍数减 1（拍数 = cmd_xlen+1）",
    "cmd_xburst": "突发类型：2'b00 FIXED 固定地址；2'b01 INCR 递增地址；2'b10 WRAP 回卷递增地址",
    "cmd_modes": "访问特权模式：0=Machine，1=Hypervisor，2=Supervisor，3=User",
    "cmd_dmode": "调试模式指示：1=调试访问，0=非调试访问",
    "cmd_attri": "传输属性：attri[0] 取指/数据（1=IFU 访问），attri[1] Device/非 Device，attri[2] 不可缓存/可缓存",
    "cmd_beat": "突发拍指示：0=非突发（或内部突发拍），1=突发首拍，2=突发末拍",
    "rsp_ready": "响应通道就绪：指示主机可接收读数据（读）或响应信息（写）",
    "rsp_valid": "响应通道有效：指示读数据/写响应已就绪，本次传输可完成",
    "rsp_err": "响应错误标志：1=本次读/写传输出错",
    "rsp_excl_ok": "独占访问成功指示：1=独占访问成功，0=失败",
    "rsp_rdata": "读数据（宽度可参数化）",
}
APB_DESC = {
    "paddr": "APB 地址：本次传输访问的地址（AMBA APB PADDR）",
    "pwrite": "读写指示：1=写，0=读（AMBA APB PWRITE）",
    "psel": "从机选择：指示选中该从机进行本次传输（AMBA APB PSEL）",
    "pprot": "保护类型：特权级、安全与取指/数据指示（AMBA APB PPROT）",
    "pstrobe": "字节写选通：每字节 1 位，PSTRB[n]=1 表示写入第 n 字节通道（AMBA APB PSTRB）",
    "penable": "传输使能：指示 APB 传输的第二个及后续周期（AMBA APB PENABLE）",
    "pwdata": "写数据（AMBA APB PWDATA）",
    "prdata": "读数据（AMBA APB PRDATA）",
    "pready": "就绪：指示从机已完成本次传输，可插入等待周期（AMBA APB PREADY）",
    "pslverr": "从机错误：指示本次传输发生错误（AMBA APB PSLVERR）",
}
AHB_DESC = {
    "htrans": "AHB-Lite 传输类型：IDLE/BUSY/NONSEQ/SEQ（HTRANS）",
    "hwrite": "写/读指示：1=写，0=读（HWRITE）",
    "hmastlock": "锁定传输：指示主机要求不间断的连续访问（HLOCK）",
    "hsize": "传输大小：每拍字节数 = 2^hsize（HSIZE）",
    "hburst": "突发类型：指示突发方式，如 SINGLE/INCR/INCR8/WRAP 等（HBURST）",
    "hprot": "保护控制：数据/取指、特权级、可缓冲/可缓存等指示（HPROT）",
    "hwdata": "写数据（HWDATA）",
    "haddr": "传输的字节地址（HADDR）",
    "hrdata": "读数据（HRDATA）",
    "hresp": "响应状态：OKAY 或 ERROR（HRESP）",
    "hready": "传输就绪：指示从机已完成当前传输（HREADY）",
}
AXI_DESC = {
    "arvalid": "读地址通道有效：主机正在驱动有效的读地址与控制信息",
    "arready": "读地址通道就绪：从机可接收读地址",
    "araddr": "读地址：读突发的起始字节地址",
    "arlen": "读突发长度：突发内数据拍数减 1（0~255）",
    "arsize": "读突发大小：每拍数据字节数 = 2^arsize",
    "arburst": "读突发类型：FIXED/INCR/WRAP",
    "arlock": "锁定类型：指示原子/独占访问属性",
    "arcache": "缓存属性：可缓存/不可缓存/设备等类型提示",
    "arprot": "保护类型：特权级、安全与取指/数据指示",
    "aruser": "用户自定义边带信号（读地址通道，8 位）",
    "rready": "读数据就绪：主机可接收读数据",
    "rvalid": "读数据有效：从机正在驱动有效的读数据",
    "rdata": "读数据",
    "rresp": "读响应状态：OKAY/EXOKAY/SLVERR/DECERR",
    "ruser": "用户自定义边带信号（读数据通道，8 位）",
    "rlast": "读最后一拍：指示读突发数据的最后一拍",
    "awvalid": "写地址通道有效：主机正在驱动有效的写地址与控制信息",
    "awready": "写地址通道就绪：从机可接收写地址",
    "awaddr": "写地址：写突发的起始字节地址",
    "awlen": "写突发长度：突发内数据拍数减 1（0~255）",
    "awsize": "写突发大小：每拍数据字节数 = 2^awsize",
    "awburst": "写突发类型：FIXED/INCR/WRAP",
    "awlock": "锁定类型：指示原子/独占访问属性",
    "awcache": "缓存属性：可缓存/不可缓存/设备等类型提示",
    "awprot": "保护类型：特权级、安全与取指/数据指示",
    "awuser": "用户自定义边带信号（写地址通道，8 位）",
    "bready": "写响应就绪：主机可接收写响应",
    "bvalid": "写响应有效：从机正在驱动有效的写响应",
    "bresp": "写响应状态：OKAY/EXOKAY/SLVERR/DECERR",
    "buser": "用户自定义边带信号（写响应通道，8 位）",
    "wready": "写数据就绪：从机可接收写数据",
    "wvalid": "写数据有效：主机正在驱动有效的写数据",
    "wdata": "写数据",
    "wstrb": "字节写选通：每字节 1 位，wstrb[n]=1 表示写入第 n 字节通道",
    "wlast": "写最后一拍：指示写突发数据的最后一拍",
}

# ============================= pad 描述 =============================
def pad_usart(pin, sfx):
    doc = {
        ("rx", "i_ival"): ("RX 引脚输入值（The input value from RX_PAD）", 0),
        ("tx", "i_ival"): ("TX 引脚输入值（The input value from TX_PAD）", 0),
        ("tx", "o_oval"): ("输出至 TX 引脚(PAD) 的输出值（The output value to TX PAD）", 0),
        ("tx", "o_oe"): ("输出至 TX 引脚(PAD) 的输出使能（The output enable to TX_PAD）", 0),
        ("tx", "o_pue"): ("输出至 TX 引脚(PAD) 的上拉使能（The pull-up enable to TX_PAD）", 0),
        ("sclk", "o_oval"): ("SCLK(TX_CLK) 引脚输出的串行时钟（The CLK output to TX_CLK_PAD）", 0),
        ("cts", "i_ival"): ("CTS 引脚输入值（The input value from CTS_PAD）", 0),
        ("rts", "o_oval"): ("输出至 RTS 引脚(PAD) 的输出值（The output value to RTS_PAD）", 0),
    }
    if (pin, sfx) in doc:
        return doc[(pin, sfx)]
    pn = {"rx": "RX", "tx": "TX", "sclk": "SCLK(TX_CLK)", "cts": "CTS", "rts": "RTS"}[pin]
    g = {
        "i_ival": "来自 %s 引脚(PAD) 的输入值" % pn,
        "o_oval": "输出至 %s 引脚(PAD) 的输出值" % pn,
        "o_oe": "输出至 %s 引脚(PAD) 的输出使能（高有效）" % pn,
        "o_pue": "输出至 %s 引脚(PAD) 的上拉使能（高有效）" % pn,
    }
    return (g[sfx], 1)

def pad_qspi(pin, sfx):
    if pin == "sck":
        d = {"i_ival": "SCK 引脚输入时钟（spi pad input clock）", "o_oval": "SCK 引脚输出时钟（spi pad output clock）", "o_oe": "SCK 引脚输出时钟使能（spi pad output clock enable）"}
    elif pin == "cs":
        d = {"i_ival": "CS 引脚输入（spi pad input cs）", "o_oval": "CS 引脚输出（spi pad output cs）", "o_oe": "CS 引脚输出使能（spi pad output cs enable）"}
    else:
        n = pin[3:]
        d = {"i_ival": "DQ%s 引脚输入数据（spi pad input data line %s）" % (n, n), "o_oval": "DQ%s 引脚输出数据（spi pad output data line %s）" % (n, n), "o_oe": "DQ%s 引脚输出数据使能（spi pad output data enable line %s）" % (n, n)}
    return (d[sfx], 0)

def pad_sai(side, pin, sfx):
    s = "saia" if side == "a" else "saib"
    if pin == "mclk":
        d = {"o_oval": "%s MCLK 输出（%s MCLK output）" % (s.upper(), s), "o_oe": "%s MCLK 输出使能（%s MCLK output enable）" % (s.upper(), s)}
    elif pin == "fs":
        d = {"i_ival": "%s FS 输入（%s FS input）" % (s.upper(), s), "o_oval": "%s FS 输出（%s FS output）" % (s.upper(), s), "o_oe": "%s FS 输出使能（%s FS output enable）" % (s.upper(), s)}
    elif pin == "sck":
        d = {"i_ival": "%s SCK 输入（%s SCK input）" % (s.upper(), s), "o_oval": "%s SCK 输出（%s SCK output）" % (s.upper(), s), "o_oe": "%s SCK 输出使能（%s SCK output enable）" % (s.upper(), s)}
    else:
        n = pin[2:]
        d = {"i_ival": "%s SD%s 输入（%s sd%s input）" % (s.upper(), n, s, n), "o_oval": "%s SD%s 输出（%s sd%s output）" % (s.upper(), n, s, n), "o_oe": "%s SD%s 输出使能（%s sd%s output enable）" % (s.upper(), n, s, n)}
    return (d[sfx], 0)

# ============================= 逐信号归类 =============================
def put(name, gid, desc, gen):
    by_name[name] = (gid, desc, gen)

unmapped = []
for name, width, direction, lineno in rows:
    if name in EXACT:
        gid = "cpu" if name.startswith(("core", "cpu", "soc_clk_core", "sync_cpu0")) else "wwdg"
        put(name, gid, *EXACT[name]); continue
    m = re.match(r"^(qspi(?:_xip0|[12]))_flash_(dw32|spare)_sel$", name)
    if m:
        if m.group(2) == "dw32":
            put(name, "qspi", "SPI Flash 4 字节地址模式选择（spi flash addr 4 byte select），使能 4 字节地址访问大容量 Flash", 0)
        else:
            put(name, "qspi", "SPI Flash 读命令 0x48 选择（spi flash read cmd 0x48 select），用于 spare 区读取", 0)
        continue
    m = re.match(r"^usart([01])_(rx|tx|sclk|cts|rts)_(i_ival|o_oval|o_oe|o_pue)$", name)
    if m:
        t, g = pad_usart(m.group(2), m.group(3))
        put(name, "usart", t, g); continue
    m = re.match(r"^qspi(?:_xip0|[12])_(sck|cs_0|dq_[0-3])_(i_ival|o_oval|o_oe)$", name)
    if m:
        pin = "cs" if m.group(1) == "cs_0" else m.group(1)
        t, g = pad_qspi(pin, m.group(2))
        put(name, "qspi", t, g); continue
    m = re.match(r"^lgpio0_gpio([0-9]+)_(i_ival|o_oval|o_oe|o_pue|o_pde|o_keep)$", name)
    if m:
        sfx = m.group(2)
        nm = {"i_ival": "输入数据（来自该 LGPIO 引脚：io_port_pins_N_i_ival）", "o_oval": "输出数据（输出至该 LGPIO 引脚）", "o_oe": "输出使能（高有效）", "o_pue": "上拉使能（高有效）", "o_pde": "下拉使能（高有效）", "o_keep": "总线保持使能（高有效）"}[sfx]
        put(name, "lgpio", "GPIO%s 引脚：%s" % (m.group(1), nm), 0); continue
    m = re.match(r"^sai0_sai0_(a|b)_(fs|sck|sd[0-3]|mclk)_(i_ival|o_oval|o_oe)$", name)
    if m:
        t, g = pad_sai(m.group(1), m.group(2), m.group(3))
        put(name, "sai", t, g); continue
    m = re.match(r"^(.*)_apb_(paddr|pwrite|psel|pprot|pstrobe|penable|pwdata|prdata|pready|pslverr)$", name)
    if m:
        put(name, "crg_apb", APB_DESC[m.group(2)], 0); continue
    m = re.match(r"^npu_ahbl_slv_async_ahbl_(htrans|hwrite|hmastlock|hsize|hburst|hprot|hwdata|haddr|hrdata|hresp|hready)$", name)
    if m:
        put(name, "npu", AHB_DESC[m.group(1)], 0); continue
    m = re.match(r"^npu_axi_mst_async_fifo_axi_([a-z0-9_]+)$", name)
    if m:
        put(name, "npu", AXI_DESC[m.group(1)], 0); continue
    m = re.match(r"^npu_axi_slv_async_fifo_axi_([a-z0-9_]+)$", name)
    if m:
        put(name, "npu", AXI_DESC[m.group(1)], 0); continue
    m = re.match(r"^(test_fab_apb_slv|sram[0-3]_ram)_icb_(cmd_[a-z_]+|rsp_[a-z_]+)$", name)
    if m:
        gid = "testfab" if m.group(1).startswith("test_fab") else "sram"
        put(name, gid, ICB_DESC[m.group(2)], 0); continue
    m = re.match(r"^sync_.+_rst_n$", name)
    if m:
        unmapped.append((name, lineno)); continue
    m = re.match(r"^(.*)_subm_pd_n$", name)
    if m:
        mod = m.group(1)
        gid = "npu" if mod.startswith("npu_") else "pwr"
        put(name, gid, "%s 子模块的电源关断控制（power down）信号，低电平有效：由 SoC 电源管理控制，用于关断/指示 %s 的电源（生成）" % (mod, mod), GEN); continue
    m = re.match(r"^(.*)_cfg_clk_en$", name)
    if m:
        mod = m.group(1)
        put(name, "pwr", "%s 的配置时钟使能（cfg_clk_en，高有效）：由 SoC 时钟管理控制，用于门控 %s 的配置时钟（生成）" % (mod, mod), GEN); continue
    m = re.match(r"^(.*)_subm_clk_en_r$", name)
    if m:
        mod = m.group(1)
        put(name, "pwr", "%s 子模块功能时钟使能（subm_clk_en_r，高有效）：由 SoC 时钟管理产生，用于门控 %s 的功能时钟（生成）" % (mod, mod), GEN); continue
    m = re.match(r"^(.*)_clk_en$", name)
    if m:
        mod = m.group(1)
        put(name, "pwr", "%s 的时钟使能（clk_en，高有效）：由 SoC 时钟管理控制，用于门控 %s 的时钟（生成）" % (mod, mod), GEN); continue
    m = re.match(r"^(udma[01]|usart[01]|qspi(?:_xip0|[12])|lgpio0|wwdg0|rtc0|sai0|idu|soc_glue|crg_apb_slv_ratio|npu_ahbl_slv|npu_axi_mst|npu_axi_slv|sram[0-3])_(cfg_clk|clk)$", name)
    if m:
        mod, k = m.group(1), m.group(2)
        gid2 = "npu" if mod.startswith("npu_") else "clk"
        if mod in MOD_CLK_DOC:
            t, g = MOD_CLK_DOC[mod]
        else:
            kw = "配置" if k == "cfg_clk" else "功能"
            t = GEN_CLK_TMPL % (mod, kw, name, mod, kw)
            g = GEN
        put(name, gid2, t, g); continue
    if name == "main_fab_clk":
        put(name, "clk", "主总线互连（main_fab）的时钟输入，由 SoC 时钟源提供（生成）", GEN); continue
    if name == "axi_fab_clk":
        put(name, "clk", "AXI 总线互连（axi_fab）的时钟输入，由 SoC 时钟源提供（生成）", GEN); continue
    if name == "rtc0_rtc_clk":
        put(name, "clk", "RTC0 的 RTC 时钟（rtc_clk：RTC clock，低频时钟，驱动 RTC 计数逻辑）", 0); continue
    if name == "sai0_sai0_sai_clk":
        put(name, "sai", "SAI0 的音频参考时钟（sai_clk），用于产生音频位时钟/帧时钟；SAI 文档未单列该行，按名称拟写（生成）", GEN); continue
    if name == "por_rst_n":
        put(name, "rst", "系统上电复位（por，低有效）：复位整个子系统，是各模块 POR 复位（含核 JTAG 逻辑复位）的源头（参考核文档 por_reset_n 语义）", 0); continue
    if name == "reset_bypass":
        put(name, "dft", "置 1 时旁路内部产生的复位（仅 por_reset_n 生效），以满足 DFT 测试规则（NA300 Table 6.1 reset_bypass）", 0); continue
    if name == "clkgate_bypass":
        put(name, "dft", "置 1 时旁路内部时钟门控（clock gater），以满足 DFT 测试规则（NA300 Table 6.1 clkgate_bypass）", 0); continue
    if name == "dftmux_bypass":
        put(name, "dft", "置 1 时旁路 DFT 测试复用逻辑（dft mux），使功能路径直通（名称推拟（生成））", GEN); continue
    if name == "scan_clk":
        put(name, "dft", "扫描测试时钟输入（scan clock），供扫描链移位使用（名称推拟（生成））", GEN); continue
    if name == "user_soc_irg":
        put(name, "irq", "SoC 用户中断请求组输入（116 位）：由 SoC 顶层汇集的用户/外部中断源，按位接入子系统内中断相关逻辑（如中断控制器/核），位定义由 SoC 集成确定（生成）", GEN); continue
    unmapped.append((name, lineno))

SYNC = {
    "sync_npu_ahbl_slv_clk_npu_ahbl_slv_async_rst_n": ("npu_ahbl_slv_async（NPU AHB-Lite 从机访问口，跨时钟域模块）的复位，低有效，在 npu_ahbl_slv_clk 域同步后输入（生成）", GEN),
    "sync_npu_axi_mst_clk_npu_axi_mst_async_fifo_rst_n": ("npu_axi_mst_async_fifo（NPU AXI 主机接口，跨时钟域模块）的复位，低有效，在 npu_axi_mst_clk 域同步后输入（生成）", GEN),
    "sync_npu_axi_slv_clk_npu_axi_slv_async_fifo_rst_n": ("npu_axi_slv_async_fifo（NPU AXI 从机接口，跨时钟域模块）的复位，低有效，在 npu_axi_slv_clk 域同步后输入（生成）", GEN),
    "sync_idu_cfg_clk_idu_rst_n": ("idu 模块的复位，低有效，在 idu_cfg_clk 域同步后输入（生成）", GEN),
    "sync_soc_glue_cfg_clk_soc_glue_rst_n": ("soc_glue 模块的复位，低有效，在 soc_glue_cfg_clk 域同步后输入（生成）", GEN),
    "sync_udma0_cfg_clk_udma0_rst_n": ("uDMA0 的复位（rst_n，低有效：Reset signal (active when low)），在 udma0_cfg_clk 域同步后输入", 0),
    "sync_udma1_cfg_clk_udma1_rst_n": ("uDMA1 的复位（rst_n，低有效：Reset signal (active when low)），在 udma1_cfg_clk 域同步后输入", 0),
    "sync_usart0_cfg_clk_usart0_rst_n": ("USART0 的复位（rst_n，低有效：Reset for usart in ICB clock domain），在 usart0_cfg_clk 域同步后输入", 0),
    "sync_usart1_cfg_clk_usart1_rst_n": ("USART1 的复位（rst_n，低有效：Reset for usart in ICB clock domain），在 usart1_cfg_clk 域同步后输入", 0),
    "sync_qspi_xip0_cfg_clk_qspi_xip0_rst_n": ("QSPI_XIP0 的复位（rst_n，低有效：Reset for spi），在 qspi_xip0_cfg_clk 域同步后输入", 0),
    "sync_qspi1_cfg_clk_qspi1_rst_n": ("QSPI1 的复位（rst_n，低有效：Reset for spi），在 qspi1_cfg_clk 域同步后输入", 0),
    "sync_qspi2_cfg_clk_qspi2_rst_n": ("QSPI2 的复位（rst_n，低有效：Reset for spi），在 qspi2_cfg_clk 域同步后输入", 0),
    "sync_lgpio0_cfg_clk_lgpio0_rst_n": ("LGPIO0 的复位（rst_n，低有效：Reset for LGPIO in ICB clock domain），在 lgpio0_cfg_clk 域同步后输入", 0),
    "sync_wwdg0_cfg_clk_wwdg0_por_rst_n": ("WWDG0 的上电复位（por_rst_n，低有效）：复位 WWDG 逻辑（含计数）；WWDG 文档未单列，按名称拟写（生成）", GEN),
    "sync_wwdg0_cfg_clk_wwdg0_icb_rst_n": ("WWDG0 的 ICB 复位（icb_rst_n，低有效）：复位 WWDG 寄存器配置逻辑（WWDG 文档提及模块由 icb_rstn 复位），在 wwdg0_cfg_clk 域同步后输入", 0),
    "sync_sai0_cfg_clk_sai0_sys_rst_n": ("SAI0 的系统复位（sys_rst_n，低有效：复位 ICB 时钟域内的 SAI），在 sai0_cfg_clk 域同步后输入", 0),
    "sync_main_fab_clk_main_fab_rst_n": ("主总线互连（main_fab）的复位，低有效，在 main_fab_clk 域同步后输入（生成）", GEN),
    "sync_axi_fab_clk_axi_fab_rst_n": ("AXI 总线互连（axi_fab）的复位，低有效，在 axi_fab_clk 域同步后输入（生成）", GEN),
    "sync_rtc0_rtc_clk_rtc0_rtc_rst_n": ("RTC0 的 RTC 域复位（rtc_rstn，低有效：RTC reset），在 rtc0_rtc_clk 域同步后输入", 0),
    "sync_rtc0_cfg_clk_rtc0_bkp_reg_rst_n": ("RTC0 备份寄存器（bkp reg）的复位，低有效，在 rtc0_cfg_clk 域同步后输入；RTC 文档未单列，按名称拟写（生成）", GEN),
    "sync_rtc0_cfg_clk_rtc0_icb_rst_n": ("RTC0 的 ICB 总线复位（icb_rstn，低有效：ICB Bus reset），在 rtc0_cfg_clk 域同步后输入", 0),
}
for n, (d, g) in SYNC.items():
    if n not in by_name:
        put(n, "npu" if n.startswith("sync_npu") else "pwr", d, g)

left = [(n, l) for (n, l) in unmapped if n not in SYNC]
if left:
    print("STILL UNMAPPED:", left)
for name, width, direction, lineno in rows:
    if name not in by_name:
        raise SystemExit("no mapping: %s line %d" % (name, lineno))

# ============================= 渲染 =============================
def emit_md_table(rs):
    out = ["| 信号名 | 位宽 | 方向 | 描述 |", "|---|---|---|---|"]
    for name, width, direction, desc, gen, lineno in rs:
        d = re.sub(r"[（(]生成[）)]", "", desc).strip()
        if gen:
            d += " **(生成)**"
        out.append("| `%s` | %s | %s | %s |" % (name, width, DIR[direction], d.replace("|", "/")))
    return out

def collect(gid):
    rs = []
    for name, width, direction, lineno in rows:
        g, d, f = by_name[name]
        if g == gid:
            rs.append((name, width, direction, d, f, lineno))
    return rs

out = ["# pd_subsys_top 顶层接口描述（信号分组与信号表）", ""]
out.append("本文档描述 **pd_subsys_top** 顶层模块对外接口。端口清单源文件：`pd_subsys_top_ports.csv`（共 %d 个信号）。" % len(rows))
out.append("")
out.append("**约定：**")
out.append("")
out.append("- **方向**均以 pd_subsys_top 模块本身为参考：输入 = 进入 pd_subsys，输出 = 由 pd_subsys 驱动（即端口清单 direction 列的直译）。")
out.append("- **描述来源**：优先取自随附 Nuclei 文档（300/NA300 核文档、InSight、Bus Fab Spec、各外设 IP 参考手册 §9 Full Signal Interface 等），中文为文档描述的意译；文档中找不到确切描述、按信号命名规律拟写的条目，在描述末尾标注 **(生成)**。")
out.append("- 总线协议信号（APB/AHB-Lite/AXI/ICB）语义遵循相应协议规范，出处可在 Bus Fab Spec §9、核文档总线接口表及外设文档寄存器配置接口表中找到，不再逐个标注。")
out.append("- 标有 (生成) 的条目仅供集成参考，正式发布前请以 RTL/集成方案为准核对。")
out.append("")
out.append("分组与章节：1 处理器核接口；2 NPU 接口；3 时钟接口；4 模块电源/时钟门控与同步复位；5 系统复位；6 测试(DFT) 接口；7 总线与存储接口（7.1 CRG APB / 7.2 Test-Fab ICB / 7.3 SRAM0~3 ICB）；8 外设 IO 接口（8.1 USART / 8.2 QSPI / 8.3 LGPIO / 8.4 SAI / 8.5 WWDG）；9 系统中断输入。")
out.append("")
out.append("---")
out.append("")

TITLES = {
    "cpu": "1. 处理器核接口（core0/core1 与 cpu0/cpu1）",
    "npu": "2. NPU 接口（时钟/复位与总线访问）",
    "clk": "3. 全局与模块时钟、总线互连时钟/复位",
    "pwr": "4. 外设/模块电源与时钟门控控制信号（汇总）",
    "rst": "5. 系统级复位接口",
    "dft": "6. 测试（DFT）控制接口",
    "crg_apb": "7.1 CRG 时钟/复位模块 APB 配置接口",
    "testfab": "7.2 Test-Fab ICB 配置接口",
    "sram": "7.3 SRAM0~SRAM3 存储接口",
    "usart": "8.1 USART0/USART1 接口",
    "qspi": "8.2 QSPI_XIP0 / QSPI1 / QSPI2 接口",
    "lgpio": "8.3 LGPIO0 接口",
    "sai": "8.4 SAI0 接口",
    "wwdg": "8.5 WWDG0 接口",
    "irq": "9. 系统中断输入接口",
}
INTROS = {
    "cpu": "本组为 pd_subsys 内 RISC-V 处理器核相关的顶层接口：核的调试接口（DMI/调试控制，TAP 置于核外，见 InSight §9.2/§9.3）、启动配置（复位向量/HART ID/复位后停止）、睡眠与低功耗指示、核内 TIMER 驱动脉冲（mtime_toggle_a）以及核的时钟/时钟使能输入。\n\n核级信号语义以《300 Product Databook》§6.15、《NA300 Core Databook》§6.1 与《InSight Specification》§9 为准；标 (生成) 者为 SoC 集成级命名信号。",
    "npu": "pd_subsys 与 NPU 之间通过异步（async）跨时钟域模块互连，共三组总线口：① npu_ahbl_slv_async：面向 NPU AHB-Lite 从机的访问口（如寄存器配置，地址 19 位）；② npu_axi_mst_async_fifo：NPU 作为 AXI 主机发起访问（256 位数据，访问系统侧存储），pd_subsys 提供从侧；③ npu_axi_slv_async_fifo：面向 NPU AXI 从机的访问口（256 位数据）。每组均带独立时钟/复位，另有电源控制信号。\n\n总线信号语义来源：Bus Fab Spec §9.2/§9.3 及核文档总线接口表；时钟/复位/电源控制为集成级命名，标 (生成)。",
    "clk": "时钟输入均来自 SoC 时钟源：main_fab_clk（主互连）、axi_fab_clk（AXI 互连）、各外设/模块配置时钟 *_cfg_clk（ICB 寄存器配置域；各模块的 clk 语义见对应 IP 文档 §9 信号表）、rtc0_rtc_clk（RTC 低频时钟）；CPU 与 NPU 相关时钟分别见第 1、2 节；互连复位 sync_main_fab_clk_main_fab_rst_n / sync_axi_fab_clk_axi_fab_rst_n 亦列于本组。标 (生成) 者为 SoC 集成级命名。",
    "pwr": "按模块（udma0/1、usart0/1、qspi_xip0/qspi1/qspi2、lgpio0、wwdg0、rtc0、sai0、idu、soc_glue、crg_apb_slv、sram0~3 等）给出电源关断（*_subm_pd_n）、配置时钟使能（*_cfg_clk_en）、功能时钟使能（*_subm_clk_en_r / *_clk_en）以及同步复位（sync_*_rst_n）输入。这类信号属于本 SoC 集成方案的时钟/复位/电源管理接口，由 SoC 侧（PMU/时钟复位控制器）驱动，未在 Nuclei IP 文档中逐一定义，描述按命名含义拟写并标 (生成)；其中目标模块复位语义取自各 IP 文档的 rst_n 说明（见信号描述括注）。",
    "rst": "por_rst_n 为子系统上电复位源（低有效），复位整个子系统；各模块/核的复位以它为源头，在各自时钟域内经同步（异步置位/同步释放）后使用（对应各 sync_*_rst_n 输入，见第 4 节及各模块组）。",
    "dft": "reset_bypass / clkgate_bypass 为复位与时钟门控的 DFT 旁路控制（NA300 Table 6.1）；dftmux_bypass、scan_clk 为集成级 DFT 复用旁路与扫描时钟（名称推拟，标 (生成)）。",
    "crg_apb": "crg_apb_slv_ratio 为时钟复位产生器（CRG）内保存分频比等配置的 APB 从机寄存器组；pd_subsys 内的时钟/复位控制逻辑作为 APB 主机通过该口配置（方向以 pd_subsys 为准：地址/控制为输出，读数据/就绪/错误为输入）。描述来源：Bus Fab Spec §9.4 APB 端口表（AMBA APB 协议信号）。",
    "testfab": "test_fab_apb_slv 为 SoC 测试总线（test fab）内的 APB 从机寄存器组，pd_subsys 以 ICB 主机方式访问（命令为输出、响应为输入），用于测试/调试相关寄存器配置。ICB 描述来源：外设文档“Register Configuration Signal Interface”表与 ICB 协议规范。",
    "sram": "sram0~sram3 为 pd_subsys 内的 4 个片内 SRAM 控制器口（256 位数据，地址 21 位），pd_subsys 内 AXI 总线侧以 ICB 主机方式访问（命令为输出、响应为输入）；各 SRAM 的电源/时钟使能/复位控制见第 3、4 节。",
    "usart": "USART0/USART1 为通用同步/异步收发器。顶层按实例引出 RX/TX/SCLK/CTS/RTS 的 pad 接口（每引脚 i_ival/o_oval/o_oe/o_pue）；其中 RX/CTS 以输入为主、TX/RTS/SCLK 以输出为主，pad 输出侧使能/上拉信号供 SoC 引脚复用单元统一控制。USART 文档信号表中逐行列出的条目直接意译（不加标）；未逐行列出、按同一文档 pad 语义补全的对称位宽条目标 (生成)。",
    "qspi": "qspi_xip0（XIP/就地执行，Flash 映射到地址空间直接取指，见 SPI 文档 XIP 章节）、qspi1、qspi2 为三个 NUQSPI 实例。顶层按实例引出 SCK/CS0/DQ0~3 pad 接口及 Flash 模式选择输入：flash_dw32_sel（4 字节地址）、flash_spare_sel（0x48 spare 读命令）。描述来源：SPI 文档 §9 信号表。",
    "lgpio": "LGPIO0 为轻量 GPIO（引脚含上拉/下拉/总线保持控制），顶层按引脚引出 GPIO0~5 的 pad 接口（i_ival/o_oval/o_oe/o_pue/o_pde/o_keep）。描述来源：LGPIO 文档 §9 信号表。",
    "sai": "SAI0 为串行音频接口（A/B 两个音频子块），顶层按子块引出 FS/SCK/SD0~3/MCLK 的 pad 接口以及音频参考时钟 sai0_sai0_sai_clk。描述来源：SAI 文档 §9 信号表（sai_clk 文档未单列，标 (生成)）。",
    "wwdg": "WWDG0 为窗口看门狗外设。顶层只引出其复位输出 wwdg0_wdogres（WWDG 文档 WDOGRES）；其余配置时钟与复位控制见第 3、4 节。",
    "irq": "user_soc_irg 为 SoC 顶层输入 pd_subsys 的用户中断请求组总线（116 位），位定义由 SoC 集成确定（与核中断口/中断控制器的连接见 SoC 集成方案），描述按名称拟写。",
}
PARENTS = {
    "bus": ("7. 总线与存储接口", "pd_subsys 对外的总线访问接口共三组：CRG 时钟复位模块的 APB 配置口（7.1）、SoC 测试总线 Test-Fab 的 ICB 配置口（7.2）、片内 SRAM0~3 的 ICB 存储口（7.3）。总线信号描述来源：Bus Fab Spec §9（APB/AHB-L/AXI/ICB 端口表）、核文档总线接口表，以及各外设文档“Register Configuration Signal Interface”（ICB）表。"),
    "io": ("8. 外设 IO 接口", "外设引出的顶层 pad 接口遵循 Nuclei pad 接口约定（<pad>_i_ival 输入值 / o_oval 输出值 / o_oe 输出使能 / o_pue 上拉使能 / o_pde 下拉使能 / o_keep 总线保持，语义见 LGPIO 文档 §9），并含 XIP/模式等配置输入；各外设的配置时钟、电源门控与复位控制见第 3、4 节。"),
}
ORDER = ["cpu", "npu", "clk", "pwr", "rst", "dft", "crg_apb", "testfab", "sram", "usart", "qspi", "lgpio", "sai", "wwdg", "irq"]
PARENT_OF = {"crg_apb": "bus", "testfab": "bus", "sram": "bus", "usart": "io", "qspi": "io", "lgpio": "io", "sai": "io", "wwdg": "io"}
emitted = set()

def sec_rows(gid):
    rs = collect(gid)
    rs.sort(key=lambda r: r[5])
    return rs

def emit_h2(t, intro):
    out.append("## " + t); out.append("")
    if intro:
        out.append(intro); out.append("")

def emit_h3(gid):
    out.append("### " + TITLES[gid]); out.append("")
    if INTROS.get(gid):
        out.append(INTROS[gid]); out.append("")
    out.extend(emit_md_table(sec_rows(gid))); out.append("")

def emit_full(gid):
    emit_h2(TITLES[gid], INTROS.get(gid, ""))
    out.extend(emit_md_table(sec_rows(gid))); out.append("")

for gid in ORDER:
    if gid == "npu":
        emit_h2(TITLES["npu"], INTROS["npu"])
        sub = {"npu_ahbl": [], "npu_axi_m": [], "npu_axi_s": [], "npu_ctrl": []}
        for r in sec_rows("npu"):
            n = r[0]
            if n.endswith(("_clk", "_rst_n", "_pd_n", "_clk_en")):
                sub["npu_ctrl"].append(r)
            elif n.startswith("npu_ahbl"):
                sub["npu_ahbl"].append(r)
            elif n.startswith("npu_axi_mst"):
                sub["npu_axi_m"].append(r)
            else:
                sub["npu_axi_s"].append(r)
        for key, title in (("npu_ahbl", "### NPU AHB-Lite 从机访问接口（npu_ahbl_slv_async）"),
                           ("npu_axi_m", "### NPU AXI 主机接口（npu_axi_mst_async_fifo，跨时钟域）"),
                           ("npu_axi_s", "### NPU AXI 从机接口（npu_axi_slv_async_fifo，跨时钟域）"),
                           ("npu_ctrl", "### NPU 接口时钟/复位/电源控制")):
            if sub[key]:
                out.append(title); out.append("")
                out.extend(emit_md_table(sub[key])); out.append("")
        continue
    parent = PARENT_OF.get(gid)
    if parent and parent not in emitted:
        emit_h2(PARENTS[parent][0], PARENTS[parent][1])
        emitted.add(parent)
    if parent:
        emit_h3(gid)
    else:
        emit_full(gid)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(out))

cnt = Counter(g for g, d, f in by_name.values())
print("total rows:", len(rows), "mapped:", len(by_name))
print("per group:", dict(cnt))
print("written:", OUT)
