#!/usr/bin/env bash
#
# build.sh - independently rebuild Gazillionaire.swf from the decompiled
# ActionScript.
#
#   1. regenerate app/src from src/decompiled + the extracted assets
#   2. compile it with the Flex 4.16.1 + AIR 32 toolchain
#
# Requirements: tools/fetch_sdk.sh has installed $ROOT/sdk, and Java is on PATH.
#
set -euo pipefail
export JAVA_TOOL_OPTIONS="${JAVA_TOOL_OPTIONS:-} -Djava.awt.headless=true"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SDK="$ROOT/sdk"
OUT="$ROOT/build/Gazillionaire.swf"

[[ -x "$SDK/bin/amxmlc" ]] || {
  echo "error: $SDK/bin/amxmlc not found." >&2
  echo "run tools/fetch_sdk.sh first." >&2
  exit 1
}
command -v java >/dev/null || { echo "error: java not on PATH" >&2; exit 1; }

echo "==> preparing buildable source tree"
python3 "$ROOT/tools/prepare_build.py"

# The document class is the generated Flex SystemManager; the application class
# itself is only referenced by name at runtime, so force-link the entry points
# plus the classes named in SystemManager.info()'s mixins list.
# Force-link all ten recovered locale bundles. Clearing -locale below prevents
# SDK bundle generation from overriding their measured literal member order.
INCLUDES="GameType,Gazillionaire,_Gazillionaire_FlexInit,\
LoadScreen_LoadScreenGraphic,CustomPreloader,LoadScreen,\
mx.styles.StyleManagerImpl,mx.managers.systemClasses.ActiveWindowManager,\
mx.messaging.config.LoaderConfig,\
en_US\$collections_properties,en_US\$components_properties,\
en_US\$containers_properties,en_US\$controls_properties,en_US\$core_properties,\
en_US\$effects_properties,en_US\$layout_properties,en_US\$skins_properties,\
en_US\$styles_properties,en_US\$utils_properties"

# CompilerAPI.batch2 scans sources in reverse order and prioritizes generate()
# over analyze2(). Generate these 37 dependency classes before their referrers
# inheritSlots in analyze3(), preserving getscopeobject 0 in their script inits.
# Conversely, GameType above must analyze before PlayerType/OpponentType
# generate, preserving findpropstrict in those two script inits.
# CustomComboBoxSkin is also explicit to preserve its already-matching init.
INCLUDES+=",GameStrings,\
Gazillionaire_PlanetBass1Class,Gazillionaire_PlanetFrac1Class,\
Gazillionaire_PlanetHork1Class,Gazillionaire_PlanetLoro1Class,\
Gazillionaire_PlanetMira1Class,Gazillionaire_PlanetNosh1Class,\
Gazillionaire_PlanetOoom1Class,Gazillionaire_PlanetPyke1Class,\
Gazillionaire_PlanetQueg1Class,Gazillionaire_PlanetStye1Class,\
Gazillionaire_PlanetTilo1Class,Gazillionaire_PlanetVexx1Class,\
Gazillionaire_PlanetXeen1Class,Gazillionaire_PlanetZile1Class,\
Gazillionaire__embed_mxml_Frame_help3_swf_987142362,\
Gazillionaire__embed_mxml_TILO1_SWF_1460587624,\
Gazillionaire__embed_mxml_VEXX1_SWF_1452207462,\
Gazillionaire__embed_mxml_b_circle_swf_437016774,\
Gazillionaire__embed_mxml_i_arrow_swf_203146964,\
Gazillionaire__embed_mxml_i_planet_swf_630432904,\
Gazillionaire__embed_mxml_i_target_swf_976591674,\
Gazillionaire__embed_mxml_stars_bg_main_swf_835323288,\
Gazillionaire__embed_mxml_stars_main_swf_1623989498,\
_class_embed_css_b_x2_dn_swf_77392359_80761093,\
_class_embed_css_b_x2_mo_swf_335978239_175555539,\
_class_embed_css_b_x2_up_swf_565934968_340354117,\
_class_embed_css_b_x2_up_swf_565934968_340354118,\
_class_embed_css_b_x3_dn_swf_1820202694_745722986,\
_class_embed_css_b_x3_mo_swf_2078788574_683813778,\
_class_embed_css_b_x3_up_swf__1986221993_1815107817,\
_class_embed_css_f_empty_swf__416068855_1574736089,\
_class_embed_css_f_endblue_swf_1667013489_1828896639,\
_class_embed_css_f_endred_swf_735613634_1127775762,\
_class_embed_css_f_full_swf_392505595_2100659351,\
_Gazillionaire_Styles,CustomComboBoxSkin,GradientBarSkin,GradientTrackSkin"

# The gradient skins cannot generate until their SDK inheritance/interface
# dependencies are ready. Preload that closure too; otherwise Gazillionaire's
# analyze3() still overtakes the two skins even with them at the end above.
# These are already-linked SDK definitions, not additional application classes.
INCLUDES+=",mx.automation.IAutomationObject,mx.core.FlexSprite,\
mx.core.IChildList,mx.core.IConstraintClient,mx.core.IDeferredInstantiationUIComponent,\
mx.core.IFlexDisplayObject,mx.core.IFlexModule,mx.core.IInvalidating,\
mx.core.ILayoutDirectionElement,mx.core.ILayoutElement,mx.core.IMXMLObject,\
mx.core.IPropertyChangeNotifier,mx.core.IRepeaterClient,mx.core.IStateClient,\
mx.core.IUIComponent,mx.core.IUID,mx.core.IVisualElement,mx.core.IVisualElementContainer,\
mx.core.UIComponent,mx.core.mx_internal,mx.graphics.GradientBase,mx.graphics.GradientEntry,\
mx.graphics.GradientStroke,mx.graphics.IFill,mx.graphics.IStroke,mx.graphics.LinearGradient,\
mx.graphics.LinearGradientStroke,mx.graphics.SolidColor,mx.graphics.SolidColorStroke,\
mx.managers.ILayoutManagerClient,mx.managers.IToolTipManagerClient,\
mx.skins.spark.ProgressBarSkin,mx.skins.spark.ProgressBarTrackSkin,\
mx.styles.IAdvancedStyleClient,mx.styles.ISimpleStyleClient,mx.styles.IStyleClient,\
mx.validators.IValidatorListener,spark.components.Group,\
spark.components.supportClasses.GroupBase,spark.components.supportClasses.Skin,\
spark.core.IGraphicElement,spark.core.IGraphicElementContainer,\
spark.core.ISharedDisplayObject,spark.core.IViewport,spark.primitives.Rect,\
spark.primitives.supportClasses.FilledElement,spark.primitives.supportClasses.GraphicElement,\
spark.primitives.supportClasses.StrokedElement,spark.skins.IHighlightBitmapCaptureClient,\
spark.skins.SparkSkin"

echo "==> compiling $OUT"
mkdir -p "$ROOT/build"
# The Flex preloader runs on frame 1 and only hands off after the playhead
# advances to frame 2 (SystemManager.deferredNextFrame bails when
# `currentFrame + 1 > totalFrames`).  A normal MXML build gets this frame
# layout for free; because we compile the generated SystemManager directly we
# must place the application class on frame 2 explicitly, with the same
# FrameLabel the original binary has.
FLEX_HOME="$SDK" AIR_HOME="$SDK" "$SDK/bin/amxmlc" \
    -source-path "$ROOT/app/src" \
    -locale= \
    "-includes=$INCLUDES" \
    "-frames.frame=Gazillionaire,Gazillionaire" \
    -default-size 760 570 \
    -default-background-color 0xFFFFFF \
    -target-player=32.0 \
    -swf-version=43 \
    -output "$OUT" \
    "$ROOT/app/src/_Gazillionaire_mx_managers_SystemManager.as"

echo "==> built $(stat -c '%s' "$OUT") bytes: $OUT"
