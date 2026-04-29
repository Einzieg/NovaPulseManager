try:
    from backend.models import Template
except ModuleNotFoundError as e:
    if e.name not in {"backend", "backend.models"}:
        raise
    from models import Template

from .paths import resolve_template_path


class Templates:
    DISCONNECTED = Template(
        name="断开连接",
        threshold=0.75,
        template_path=resolve_template_path("identify_in/disconnected.png"),
    )
    SIGN_BACK_IN = Template(
        name="重新登录",
        threshold=0.75,
        template_path=resolve_template_path("identify_in/sign_back_in.png"),
    )
    IN_BATTLE = Template(
        name="战斗中",
        threshold=0.85,
        template_path=resolve_template_path("identify_in/in_battle.png"),
    )
    CONFIRM_RELOGIN = Template(
        name="确认重新登录",
        threshold=0.75,
        template_path=resolve_template_path("button/button_confirm_relogin.png"),
    )
    SPACE_STATION = Template(
        name="空间站",
        threshold=0.75,
        template_path=resolve_template_path("button/space_station.png"),
    )
    STAR_SYSTEM = Template(
        name="星系",
        threshold=0.75,
        template_path=resolve_template_path("button/star_system.png"),
    )
    NEBULA = Template(
        name="星云",
        threshold=0.75,
        template_path=resolve_template_path("button/nebula.png"),
    )
    ALLIANCE = Template(
        name="联盟",
        threshold=0.75,
        template_path=resolve_template_path("system/alliance.png"),
    )
    TO_SYSTEM = Template(
        name="系统按钮",
        threshold=0.85,
        template_path=resolve_template_path("button/button_system.png")
    )
    MORE_SYSTEM = Template(
        name="系统更多",
        threshold=0.85,
        template_path=resolve_template_path("button/button_more_system.png")
    )

    MENUS = [
        Template(
            name="金菜单",
            threshold=0.85,
            template_path=resolve_template_path("button/button_system_gold.png"),
        ),
        Template(
            name="蓝菜单",
            threshold=0.85,
            template_path=resolve_template_path("button/button_system_blue.png"),
        ),
    ]
    FLEETS_MENU = Template(
        name="舰队菜单",
        threshold=0.85,
        template_path=resolve_template_path("button/fleets_menu.png"),
    )
    HOVER_RECALL = Template(
        name="悬停召回",
        threshold=0.85,
        template_path=resolve_template_path("button/hover_recall.png"),
    )
    CLOSE_BUTTONS = [
        Template(
            name="关闭按钮1",
            threshold=0.8,
            template_path=resolve_template_path("button/btn_close1.png"),
        ),
        Template(
            name="关闭按钮2",
            threshold=0.8,
            template_path=resolve_template_path("button/btn_close2.png"),
        ),
        Template(
            name="关闭按钮3",
            threshold=0.8,
            template_path=resolve_template_path("button/btn_close3.png"),
        ),
        Template(
            name="关闭按钮4",
            threshold=0.8,
            template_path=resolve_template_path("button/btn_close4.png"),
        ),
        Template(
            name="关闭按钮5",
            threshold=0.8,
            template_path=resolve_template_path("button/btn_close5.png"),
        ),
    ]
    TO_HOME = Template(
        name="返回主页",
        threshold=0.85,
        template_path=resolve_template_path("button/to_home.png"),
    )
    WRECKAGE_LIST = [
        Template(
            name="精英残骸",
            threshold=0.68,
            template_path=resolve_template_path("acquisition/elite_wreckage.png"),
            forbidden=True,
        ),
        Template(
            name="合金残骸",
            threshold=0.68,
            template_path=resolve_template_path("acquisition/alloy_wreckage.png"),
            forbidden=True,
        ),
        # Template(
        #     name="水晶残骸",
        #     threshold=0.75,
        #     template_path=resolve_template_path("acquisition/crystal_wreckage.png"),
        #     forbidden=True,
        # ),
    ]
    RECALL = Template(
        name="召回",
        threshold=0.75,
        template_path=resolve_template_path("button/recall.png"),
    )
    IN_SHORTCUT = Template(
        name="处于快捷菜单",
        threshold=0.75,
        template_path=resolve_template_path("identify_in/in_menu.png"),
    )
    NO_WORKSHIPS = Template(
        name="无可用工程船",
        threshold=0.75,
        template_path=resolve_template_path("acquisition/none_available.png"),
    )

    MONSTER_NORMAL_LIST = [
        Template(
            name="2级普通精英",
            threshold=0.75,
            template_path=resolve_template_path("monsters/normal_lv2.png"),
            forbidden=True,
        ),
        Template(
            name="3级普通精英",
            threshold=0.75,
            template_path=resolve_template_path("monsters/normal_lv3.png"),
            forbidden=True,
        ),
        Template(
            name="4级普通精英",
            threshold=0.75,
            template_path=resolve_template_path("monsters/normal_lv4.png"),
            forbidden=True,
        ),
    ]

    MONSTER_ELITE_LIST = [
        Template(
            name="6级首领",
            threshold=0.75,
            template_path=resolve_template_path("monsters/leader_lv6.png"),
            forbidden=True,
        ),
        Template(
            name="5级首领",
            threshold=0.75,
            template_path=resolve_template_path("monsters/leader_lv5.png"),
            forbidden=True,
        ),
        Template(
            name="4级首领",
            threshold=0.75,
            template_path=resolve_template_path("monsters/leader_lv4.png"),
            forbidden=True,
        ),
        Template(
            name="6级精英",
            threshold=0.75,
            template_path=resolve_template_path("monsters/elite_lv6.png"),
            forbidden=True,
        ),
        Template(
            name="5级精英",
            threshold=0.75,
            template_path=resolve_template_path("monsters/elite_lv5.png"),
            forbidden=True,
        ),
    ]

    MONSTER_RED_LIST = [
        Template(
            name="流浪",
            threshold=0.75,
            template_path=resolve_template_path("red_invade/wandering.png"),
            forbidden=True,
        ),
        Template(
            name="4级运输",
            threshold=0.75,
            template_path=resolve_template_path("red_invade/lv4_red_transport.png"),
            forbidden=True,
        ),
        Template(
            name="6级节点",
            threshold=0.75,
            template_path=resolve_template_path("red_invade/lv6_node.png"),
            forbidden=True,
        ),
    ]

    COLLECT = Template(
        name="采集按钮",
        threshold=0.85,
        template_path=resolve_template_path("button/button_collect.png"),
    )

    ATTACK_BUTTON = Template(
        name="攻击",
        threshold=0.85,
        template_path=resolve_template_path("attack/attack.png")
    )
    SELECTALL = Template(
        name="全选",
        threshold=0.85,
        template_path=resolve_template_path("attack/select_all.png")
    )
    CONFIRM_ATTACK = Template(
        name="确认攻击",
        threshold=0.85,
        template_path=resolve_template_path("attack/confirm_attack.png")
    )
    REVENGE = Template(
        name="复仇",
        threshold=0.85,
        template_path=resolve_template_path("attack/revenge.png")
    )
    REVENGE_ATTACK = Template(
        name="复仇攻击",
        threshold=0.85,
        template_path=resolve_template_path("attack/revenge_attack.png")
    )
    REPAIR = Template(
        name="快速维修",
        threshold=0.65,
        template_path=resolve_template_path("button/quick_repair.png")
    )
