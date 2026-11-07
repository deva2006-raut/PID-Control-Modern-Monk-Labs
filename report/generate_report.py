"""
Automated Technical PDF Report Generator.

Generates:
    report/technical_report.pdf (Exact 15-Page Publication Document)

Applies rigorous formatting:
- Zero raw LaTeX commands in text (all math formatted using ReportLab-compliant HTML/Unicode).
- Every table cell wrapped in Paragraph flowables to prevent text truncation/clipping.
- Formatted monospace Preformatted code block with preserved indentation on Page 14.
- Exact page budgeting: 15 pages strictly preserved.
"""

import os
import sys

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    PageBreak,
    Preformatted,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and stamp 'Page X of Y' and running headers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#444444"))

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 758, "MODERN MONK LABS  |  Physical AI Research Intern Technical Report")
            self.drawRightString(576, 758, "PROJECT: PID Control Technical Assignment")
            self.setStrokeColor(colors.HexColor("#d0d0d0"))
            self.setLineWidth(0.6)
            self.line(36, 752, 576, 752)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#d0d0d0"))
        self.setLineWidth(0.6)
        self.line(36, 36, 576, 36)
        self.drawString(36, 25, "Confidential — Modern Monk Labs Physical AI Evaluation")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 25, page_str)

        self.restoreState()


def build_pdf(filename: str, plots_dir: str):
    """Build the comprehensive, publication-quality technical report."""
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=44,
        bottomMargin=44,
    )

    styles = getSampleStyleSheet()

    # Typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=19,
        leading=23,
        textColor=colors.HexColor("#0f2a4a"),
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13.5,
        textColor=colors.HexColor("#2a5c99"),
        spaceAfter=6,
    )

    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.0,
        leading=10.5,
        textColor=colors.HexColor("#555555"),
        spaceAfter=8,
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=15.5,
        textColor=colors.HexColor("#0f2a4a"),
        spaceBefore=7,
        spaceAfter=4,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12.5,
        textColor=colors.HexColor("#1f4e79"),
        spaceBefore=5,
        spaceAfter=3,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=11.2,
        textColor=colors.HexColor("#222222"),
        spaceAfter=4,
    )

    bullet_style = ParagraphStyle(
        "BulletCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=11.0,
        textColor=colors.HexColor("#222222"),
        leftIndent=10,
        spaceAfter=2.5,
    )

    callout_style = ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.0,
        leading=10.8,
        textColor=colors.HexColor("#0c345b"),
    )

    tbl_hdr_style = ParagraphStyle(
        "TableHdr",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.2,
        leading=9.0,
        textColor=colors.white,
        alignment=0,
    )

    tbl_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.2,
        leading=9.2,
        textColor=colors.HexColor("#222222"),
        alignment=0,
    )

    tbl_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.2,
        leading=9.2,
        textColor=colors.HexColor("#222222"),
        alignment=0,
    )

    code_block_style = ParagraphStyle(
        "CodeBlockStyle",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=6.8,
        leading=8.6,
        textColor=colors.HexColor("#1b395b"),
    )

    story = []

    def make_callout(text: str):
        p = Paragraph(f"<b>Key Engineering Takeaway:</b> {text}", callout_style)
        t = Table([[p]], colWidths=[540])
        t.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef4fc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#b8d3f2")),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        return t

    def add_plot(img_name: str, width: float = 520, height: float = 230):
        path = os.path.join(plots_dir, img_name)
        if os.path.exists(path):
            img = Image(path, width=width, height=height)
            return img
        else:
            return Paragraph(f"[Missing plot: {img_name}]", body_style)

    def create_wrapped_table(raw_data, col_widths, custom_styles=None):
        """Converts raw strings into wrapped Paragraph flowables to prevent text clipping."""
        wrapped_data = []
        for row_idx, row in enumerate(raw_data):
            wrapped_row = []
            for col_idx, cell in enumerate(row):
                if row_idx == 0:
                    p = Paragraph(str(cell), tbl_hdr_style)
                else:
                    if col_idx == 0:
                        p = Paragraph(str(cell), tbl_cell_bold)
                    else:
                        p = Paragraph(str(cell), tbl_cell_style)
                wrapped_row.append(p)
            wrapped_data.append(wrapped_row)

        t = Table(wrapped_data, colWidths=col_widths)
        base_style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f2a4a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]
        if custom_styles:
            base_style.extend(custom_styles)
        t.setStyle(TableStyle(base_style))
        return t

    # =========================================================================
    # PAGE 1: TITLE, EXECUTIVE SUMMARY & SECTION 1
    # =========================================================================
    story.append(Paragraph("MODERN MONK LABS — PHYSICAL AI RESEARCH INTERNSHIP", subtitle_style))
    story.append(Paragraph("PID Control: From Mathematical Principles to Robust Robotics Hardware Implementation", title_style))
    story.append(Paragraph("<b>Author:</b> Candidate: Devanshu Raut  |  <b>Target System:</b> Second-Order Mass-Spring-Damper  |  <b>Runtime:</b> Python 3.10+ (NumPy, Matplotlib)", meta_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0f2a4a"), spaceAfter=7))

    story.append(Paragraph("Executive Summary & Project Scope", h1_style))
    story.append(Paragraph(
        "In Physical AI, autonomous machines cannot operate reliably on raw perception alone. The gap between digital algorithmic decisions and physical reality is bridged by closed-loop feedback control. This technical report presents a ground-up, production-grade realization of a Proportional-Integral-Derivative (PID) control architecture engineered without external control toolboxes. We model, simulate, and validate the system on an assigned second-order physical plant (<i>m</i> = 1.0 kg, <i>c</i> = 10.0 N·s/m, <i>k</i> = 20.0 N/m) under hard actuator constraints (&plusmn;30 N). Furthermore, we expose, quantify, and resolve four fatal real-world hardware non-idealities: integral windup, sensor jitter chatter, derivative kick, and discretization latency. Finally, classical Ziegler-Nichols system identification is applied and critically evaluated.",
        body_style
    ))

    story.append(Paragraph("Section 1: The PID Concept, Daily-Life Analogy & Architecture", h1_style))
    story.append(Paragraph(
        "<b>The Intuitive Analogy (Automobile Highway Cruise Control):</b> Imagine driving a car up a steep mountain highway with target speed 100 km/h.",
        body_style
    ))
    story.append(Paragraph("• <b>Proportional Action (<i>P</i>):</b> Determines <i>how far off you are right now</i>. If the vehicle slows to 80 km/h (error = 20 km/h), the driver steps down firmly on the accelerator pedal. If error is small, the corrective push is small.", bullet_style))
    story.append(Paragraph("• <b>Integral Action (<i>I</i>):</b> Determines <i>how long you have been falling short</i>. As the vehicle climbs the steep grade, gravity pulls backward. A purely proportional throttle creates a stalemate where engine thrust balances gravity at 92 km/h. The integral term continuously sums this persistent error over time, gradually depressing the pedal until the car reaches exactly 100 km/h.", bullet_style))
    story.append(Paragraph("• <b>Derivative Action (<i>D</i>):</b> Determines <i>how rapidly you are closing the gap</i>. As the car rushes toward 100 km/h at high acceleration, the derivative senses the closing rate and eases off the throttle ahead of time, preventing sudden overshoot.", bullet_style))

    story.append(Spacer(1, 4))
    story.append(add_plot("00_feedback_loop_diagram.png", width=530, height=185))
    story.append(Paragraph("<i>Figure 1: Full closed-loop feedback architecture showing reference setpoint, controller with protective filters, saturation bounds, continuous physical plant, and sensor feedback.</i>", meta_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: SECTION 2 (MATHEMATICAL FORMULATION & DISCRETIZATION)
    # =========================================================================
    story.append(Paragraph("Section 2: Mathematical Formulation, Dimensional Units & Discrete Implementation", h1_style))
    story.append(Paragraph(
        "In continuous time, the standard textbook PID control law generates actuator command <i>u</i>(<i>t</i>) from tracking error <i>e</i>(<i>t</i>) = <i>r</i>(<i>t</i>) - <i>y</i>(<i>t</i>):",
        body_style
    ))
    story.append(Paragraph(
        "<font size='9.5'><b><i>u</i>(<i>t</i>) = <i>K</i><sub>p</sub> · <i>e</i>(<i>t</i>) + <i>K</i><sub>i</sub> · &int;<sub>0</sub><sup><i>t</i></sup> <i>e</i>(&tau;) <i>d&tau;</i> + <i>K</i><sub>d</sub> · [<i>de</i>(<i>t</i>) / <i>dt</i>]</b></font>",
        ParagraphStyle("Eq", parent=body_style, alignment=1, spaceBefore=4, spaceAfter=6, fontName="Helvetica-Bold")
    ))

    story.append(Paragraph("Physical Dimensional Unit Analysis (SI Consistency)", h2_style))
    story.append(Paragraph(
        "In physical robotics, control gains are not dimensionless scalars; they are physical transfer coefficients connecting displacement errors in metres [m] to output forces in Newtons [N]:",
        body_style
    ))

    unit_data = [
        ["Symbol", "Parameter Name", "SI Units", "Physical Interpretation in Mechanics"],
        ["e(t)", "Tracking Error", "m (metres)", "Instantaneous spatial deviation between target and cart position."],
        ["Kp", "Proportional Gain", "N / m", "Acts as an artificial software spring pulling the cart toward target."],
        ["Ki", "Integral Gain", "N / (m·s)", "Accumulates persistent historical error to eliminate static spring droop."],
        ["Kd", "Derivative Gain", "N·s / m", "Acts as an artificial viscous damper (shock absorber) opposing velocity."],
        ["u(t)", "Control Force", "N (Newtons)", "Total net force commanded to the electromechanical actuator."],
    ]
    story.append(create_wrapped_table(unit_data, [45, 105, 80, 310]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Discrete-Time Digital Computer Implementation", h2_style))
    story.append(Paragraph(
        "Embedded microcontrollers cannot execute continuous calculus. Time is sliced into discrete ticks <i>t</i><sub>k</sub> = <i>k</i>·&Delta;<i>t</i>. Numerical integration and differentiation must be approximated:",
        body_style
    ))
    story.append(Paragraph("<b>1. Proportional Term:</b> Direct algebraic evaluation: <code>P[k] = Kp * e[k]</code>", bullet_style))
    story.append(Paragraph("<b>2. Integral Term (Accumulator):</b> Discrete summation using the actual elapsed time step &Delta;<i>t</i>:", bullet_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;<code>I[k] = I[k-1] + Ki * e[k] * dt</code> (Forward/Backward Euler Rectangular Rule)", ParagraphStyle("cd1", parent=body_style, fontName="Courier", fontSize=7.2, spaceAfter=3)))
    story.append(Paragraph("<b>3. Derivative Term:</b> Discrete backward difference on measurement to eliminate kick:", bullet_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;<code>D_raw[k] = -Kd * (y[k] - y[k-1]) / dt</code>", ParagraphStyle("cd2", parent=body_style, fontName="Courier", fontSize=7.2, spaceAfter=3)))
    story.append(Paragraph("<b>4. Guardrails & Clamping:</b> Total force is bounded to [-30 N, +30 N] to prevent mathematical commands exceeding physical limits.", bullet_style))

    story.append(Spacer(1, 4))
    story.append(make_callout(
        "Dimensional consistency is the first defense in robotics. Because Kp has units of N/m and Kd has units of N·s/m, tuning a PID controller is physically equivalent to selecting the stiffness and damping of a virtual mechanical suspension attached to the target coordinate."
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: SECTION 3 (PHYSICAL PLANT MODELING & EQUILIBRIUM PROOF)
    # =========================================================================
    story.append(Paragraph("Section 3: Physical Plant Modeling & Equilibrium Analysis", h1_style))
    story.append(Paragraph(
        "The physical system is a 1-Degree-of-Freedom mass attached to a fixed wall via a linear spring and viscous dashpot damper, driven by horizontal control force <i>u</i>(<i>t</i>):",
        body_style
    ))
    story.append(Paragraph(
        "<font size='9.5'><b><i>m</i> · <i>d</i><sup>2</sup><i>x</i>(<i>t</i>)/<i>dt</i><sup>2</sup> + <i>c</i> · <i>dx</i>(<i>t</i>)/<i>dt</i> + <i>k</i> · <i>x</i>(<i>t</i>) = <i>u</i>(<i>t</i>)</b></font>",
        ParagraphStyle("Eq2", parent=body_style, alignment=1, spaceBefore=3, spaceAfter=5, fontName="Helvetica-Bold")
    ))
    story.append(Paragraph(
        "Assigned parameters: Mass <i>m</i> = 1.0 kg, Viscous Damping <i>c</i> = 10.0 N·s/m, Spring Constant <i>k</i> = 20.0 N/m, Target Setpoint <i>r</i> = 1.0 m.",
        body_style
    ))

    story.append(Paragraph("Why Holding at 1.0 m Requires Exactly 20 N (Equilibrium Proof)", h2_style))
    story.append(Paragraph(
        "By definition, mechanical steady state (equilibrium) occurs when all transient motion has completely decayed. The cart has settled motionless at displacement <i>x</i><sub>ss</sub> = 1.0 m:",
        body_style
    ))
    story.append(Paragraph("• Steady-state velocity: <b>dx/dt = 0</b>  =>  Damper resisting force = <b>c · 0 = 0 N</b>", bullet_style))
    story.append(Paragraph("• Steady-state acceleration: <b>d<sup>2</sup>x/dt<sup>2</sup> = 0</b>  =>  Inertial reaction force = <b>m · 0 = 0 N</b>", bullet_style))
    story.append(Paragraph("• Spring displacement: <b>x = 1.0 m</b>  =>  Hooke's restoring force = <b>k · x = 20.0 N/m × 1.0 m = 20.0 N</b>", bullet_style))
    story.append(Paragraph(
        "Substituting into Newton's differential equation: 1.0(0) + 10.0(0) + 20.0(1.0) = <i>u</i><sub>ss</sub> &implies; <b><i>u</i><sub>ss</sub> = 20.0 N</b>. At <i>x</i> = 1.0 m, the stretched spring exerts 20.0 N of tension pulling back toward <i>x</i> = 0. If the controller outputs any force below 20.0 N, equilibrium is broken.",
        body_style
    ))

    story.append(Paragraph("Open-Loop Dynamics: Natural Frequency & Overdamped Analysis", h2_style))
    story.append(Paragraph(
        "The open-loop characteristic equation is <i>s</i><sup>2</sup> + (<i>c/m</i>)<i>s</i> + (<i>k/m</i>) = <i>s</i><sup>2</sup> + 10<i>s</i> + 20 = 0.",
        body_style
    ))
    story.append(Paragraph("• <b>Undamped Natural Frequency:</b> <i>&omega;</i><sub>n</sub> = &radic;(<i>k/m</i>) = &radic;20.0 = <b>4.472 rad/s</b>", bullet_style))
    story.append(Paragraph("• <b>Damping Ratio:</b> <i>&zeta;</i> = <i>c</i> / (2&radic;(<i>mk</i>)) = 10.0 / (2&radic;20) = <b>1.118 > 1.0</b> (Strictly Overdamped)", bullet_style))
    story.append(Paragraph("Because <i>&zeta;</i> > 1, the open-loop plant cannot oscillate; it has two real decay poles: <i>s</i><sub>1</sub> = -2.764 s<sup>-1</sup> and <i>s</i><sub>2</sub> = -7.236 s<sup>-1</sup>.", body_style))

    story.append(Spacer(1, 3))
    story.append(add_plot("00_open_loop_response.png", width=520, height=195))
    story.append(Paragraph("<i>Figure 2: Open-loop dynamics: free decay from 1.0 m (blue), step force of 10 N settling at 0.5 m (orange), and step force of 20 N settling at 1.0 m (green). Right panel compares Runge-Kutta 4 vs. Forward Euler.</i>", meta_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: SECTION 4 (TIME-DOMAIN PERFORMANCE METRICS DEFINITION)
    # =========================================================================
    story.append(Paragraph("Section 4: Step-Response Performance Metrics Definition", h1_style))
    story.append(Paragraph(
        "To evaluate controllers quantitatively, control engineers rely on four standard time-domain metrics defined on the unit step response curve <i>y</i>(<i>t</i>) relative to target setpoint <i>r</i> = 1.0 m:",
        body_style
    ))

    story.append(Paragraph("<b>1. Rise Time (<i>t</i><sub>r</sub>, 10% to 90%):</b> The time elapsed between when the response first reaches 10% of the target (<i>y</i> = 0.10 m) and when it first crosses 90% (<i>y</i> = 0.90 m). Quantifies initial actuation speed.", bullet_style))
    story.append(Paragraph("<b>2. Peak Overshoot (<i>M</i><sub>p</sub> in %):</b> The maximum percentage by which the response exceeds the target setpoint: <i>M</i><sub>p</sub> = max(0, (<i>y</i><sub>max</sub> - <i>r</i>) / <i>r</i> &times; 100%). High overshoot indicates poor damping and causes mechanical collisions.", bullet_style))
    story.append(Paragraph("<b>3. Settling Time (<i>t</i><sub>s</sub>, 2% Band):</b> The earliest time after which the response enters and <i>permanently remains</i> within the &plusmn;2% error envelope: [0.98<i>r</i>, 1.02<i>r</i>] = [0.98 m, 1.02 m].", bullet_style))
    story.append(Paragraph("<b>4. Steady-State Error (<i>e</i><sub>ss</sub>):</b> The permanent offset remaining after transient oscillations have fully decayed: <i>e</i><sub>ss</sub> = |<i>r</i> - <i>y</i>(&infin;)|.", bullet_style))

    story.append(Spacer(1, 4))
    story.append(add_plot("04_annotated_metrics_definition.png", width=520, height=265))
    story.append(Paragraph("<i>Figure 3: Explicit graphical annotation of Rise Time (10% to 90%), Peak Overshoot (Mp), Settling Time (2% corridor), and Steady-State Error (ess) on an illustrative step response.</i>", meta_style))

    story.append(Spacer(1, 4))
    story.append(make_callout(
        "If a controller suffers from severe steady-state droop and settles below 0.90 m (e.g. pure P-control with Kp = 20 N/m settling at 0.50 m), Rise Time is mathematically undefined (reported as N/A) because the 90% threshold is never reached."
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 5: SECTION 5 (PROPORTIONAL CONTROL EXPLORATION & PROOF OF DROOP)
    # =========================================================================
    story.append(Paragraph("Section 5: Proportional-Only Control Exploration & Steady-State Droop Proof", h1_style))
    story.append(Paragraph(
        "Proportional control represents the simplest feedback mechanism: <i>u</i>(<i>t</i>) = <i>K</i><sub>p</sub> · <i>e</i>(<i>t</i>) = <i>K</i><sub>p</sub> (<i>r</i> - <i>x</i>(<i>t</i>)).",
        body_style
    ))

    story.append(Paragraph("Four Practical Strengths of Proportional Control", h2_style))
    story.append(Paragraph("1. <b>Computational Simplicity:</b> Zero state memory or historical accumulation; executes instantaneously on minimal microcontrollers.", bullet_style))
    story.append(Paragraph("2. <b>Instantaneous Phase Response:</b> Introduces zero phase lag, acting immediately upon instantaneous position errors.", bullet_style))
    story.append(Paragraph("3. <b>Zero Risk of Windup:</b> Because there is no integrator, output saturation cannot induce post-saturation lag or windup overshoot.", bullet_style))
    story.append(Paragraph("4. <b>Tunable Artificial Stiffness:</b> Directly controls closed-loop system bandwidth and disturbance rejection stiffness.", bullet_style))

    story.append(Paragraph("Mathematical Proof of Steady-State Error (Why P-Only Stops Short)", h2_style))
    story.append(Paragraph(
        "At steady state (<i>x</i> = <i>x</i><sub>ss</sub>, <i>dx/dt</i> = 0, <i>d<sup>2</sup>x/dt<sup>2</sup></i> = 0), the proportional force must exactly balance the physical spring restoring force:",
        body_style
    ))
    story.append(Paragraph(
        "<i>K</i><sub>p</sub> · (<i>r</i> - <i>x</i><sub>ss</sub>) = <i>k</i> · <i>x</i><sub>ss</sub>   &implies;   <i>K</i><sub>p</sub> · <i>r</i> = (<i>K</i><sub>p</sub> + <i>k</i>) · <i>x</i><sub>ss</sub>   &implies;   <b><i>x</i><sub>ss</sub> = [ <i>K</i><sub>p</sub> / (<i>K</i><sub>p</sub> + <i>k</i>) ] · <i>r</i></b>",
        ParagraphStyle("Eq3", parent=body_style, alignment=1, spaceBefore=3, spaceAfter=5, fontName="Helvetica-Bold")
    ))
    story.append(Paragraph(
        "Because <i>k</i> = 20.0 N/m > 0, the ratio <i>K</i><sub>p</sub> / (<i>K</i><sub>p</sub> + 20) is <b>strictly less than 1.0</b> for any finite gain <i>K</i><sub>p</sub>. To reach <i>x</i> = 1.0 m, the error must be zero (<i>e</i> = 0). But if <i>e</i> = 0, the controller outputs <i>u</i> = <i>K</i><sub>p</sub>(0) = 0 N, causing the spring to pull the cart back. Hence, pure proportional control stops short.",
        body_style
    ))

    story.append(Paragraph("Numerical Verification: Theory vs. Runge-Kutta 4 Simulation", h2_style))
    p_data = [
        ["Gain Kp (N/m)", "Theoretical x_ss (m)", "Simulated x_ss (m)", "Steady-State Error ess (m)", "Discrepancy"],
        ["20.0", "0.5000", "0.5000", "0.5000 (50.0%)", "0.000000 m (Exact)"],
        ["50.0", "0.7143", "0.7143", "0.2857 (28.6%)", "0.000000 m (Exact)"],
        ["100.0", "0.8333", "0.8333", "0.1667 (16.7%)", "0.000000 m (Exact)"],
        ["200.0", "0.9091", "0.9091", "0.0909 (9.1%)", "0.000000 m (Exact)"],
    ]
    story.append(create_wrapped_table(p_data, [85, 110, 110, 125, 110]))

    story.append(Spacer(1, 4))
    story.append(add_plot("01_p_gain_sweep.png", width=520, height=200))
    story.append(Paragraph("<i>Figure 4: Proportional-only step responses for Kp in [20, 50, 100, 200] N/m. Dotted lines indicate theoretical asymptotes matching simulation with 0.000000 m discrepancy.</i>", meta_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 6: SECTION 5 CONT. (ADDING INTEGRAL AND DERIVATIVE ACTIONS)
    # =========================================================================
    story.append(Paragraph("Section 5 (Cont.): Adding Integral and Derivative Actions", h1_style))

    story.append(Paragraph("How Integral Action Eliminates Steady-State Droop", h2_style))
    story.append(Paragraph(
        "Integral control accumulates past tracking error: <i>I</i>(<i>t</i>) = <i>K</i><sub>i</sub> &int;<sub>0</sub><sup><i>t</i></sup> <i>e</i>(&tau;) <i>d&tau;</i>. Even if position error <i>e</i>(<i>t</i>) becomes minuscule, as long as error remains non-zero, the integrator continuously sums force. At steady state, while <i>P</i> = 0 (since <i>e</i> = 0), the integral term stores exactly the 20.0 N of force required to counter Hooke's spring.",
        body_style
    ))
    story.append(add_plot("01_i_gain_sweep.png", width=520, height=185))
    story.append(Paragraph("<i>Figure 5: Integral gain sweep (Ki = 0 to 100 N/(m·s), fixed Kp = 100). Higher Ki drives steady-state error to zero progressively faster.</i>", meta_style))

    story.append(Paragraph("How Derivative Action Affects Bouncing & Oscillation", h2_style))
    story.append(Paragraph(
        "Derivative control acts as an artificial shock absorber: <i>D</i>(<i>t</i>) = -<i>K</i><sub>d</sub> (<i>dy/dt</i>). When the mass moves forward at velocity <i>v</i>, the derivative term subtracts <i>K</i><sub>d</sub> · <i>v</i> from the motor command, braking the cart before it can overshoot the target.",
        body_style
    ))
    story.append(add_plot("01_d_gain_sweep.png", width=520, height=185))
    story.append(Paragraph("<i>Figure 6: Derivative gain sweep (Kd = 0 to 30 N·s/m, fixed Kp = 100, Ki = 80). Demonstrates active suppression of oscillation and tuning of damping.</i>", meta_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 7: SECTION 6 (MASTER 4-CONTROLLER BENCHMARK COMPARISON)
    # =========================================================================
    story.append(Paragraph("Section 6: Comprehensive Benchmark Comparison (P vs. PI vs. PD vs. Full PID)", h1_style))
    story.append(Paragraph(
        "To rigorously quantify the contribution of each term, all four controller topologies were simulated on the identical physical plant (<i>m</i> = 1, <i>c</i> = 10, <i>k</i> = 20) under actuator saturation limit &plusmn;30 N for 6.0 seconds (&Delta;<i>t</i> = 0.005 s):",
        body_style
    ))

    bench_data = [
        ["Controller", "Gains (Kp, Ki, Kd)", "Rise Time tr (s)", "Overshoot Mp (%)", "Settling Time ts (s)", "SSE ess (m)", "Status"],
        ["P Controller", "(100, 0, 0)", "N/A*", "0.00%", "N/A**", "0.1667 m", "Stalls at 0.833 m"],
        ["PI Controller", "(100, 80, 0)", "0.435 s", "0.00%", "3.505 s", "0.0038 m", "Eliminates SSE"],
        ["PD Controller", "(100, 0, 15)", "N/A*", "0.00%", "N/A**", "0.1667 m", "Damped, stalls"],
        ["Full PID Controller", "(100, 80, 15)", "0.695 s", "0.00%", "2.435 s", "0.0013 m", "Optimal Benchmark"],
    ]
    story.append(create_wrapped_table(bench_data, [95, 95, 75, 75, 80, 65, 55]))
    story.append(Paragraph("<font size='7'>* N/A: Never reaches 90% setpoint due to steady-state droop. ** N/A: Never enters ±2% tolerance corridor [0.98 m, 1.02 m].</font>", meta_style))

    story.append(add_plot("01_baseline_comparison.png", width=520, height=270))
    story.append(Paragraph("<i>Figure 7: Master step response comparison: Top panel shows position trajectory x(t) relative to target and ±2% band; Bottom panel shows commanded force u(t) with ±30 N actuator saturation rails and 20 N steady-state equilibrium force line.</i>", meta_style))

    story.append(make_callout(
        "The Full PID controller achieves a 1.07-second faster settling time than the PI controller (2.435 s vs. 3.505 s) while holding steady-state error to 1.3 mm, proving that derivative damping enables faster integral convergence."
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 8: SECTION 7 - PART A (ACTUATOR SATURATION & ANTI-WINDUP)
    # =========================================================================
    story.append(Paragraph("Section 7 (Part A): Actuator Saturation (±30 N) & Integral Anti-Windup", h1_style))
    story.append(Paragraph(
        "<b>The Fatal Real-World Flaw:</b> All physical actuators have finite limits. Our motor cannot generate more than &plusmn;30.0 N. During large transient errors, the unconstrained controller demands 100 N. While the motor is pegged at its ceiling (+30 N), a naive integrator continues accumulating error: &int; <i>e dt</i>. By the time the cart crosses 1.0 m, the internal integral accumulator has wound up to <b>+34.55 N</b>. The motor refuses to decelerate because it takes seconds of reverse error to unwind this excess charge, causing massive overshoot (12.90%) and dangerous collisions.",
        body_style
    ))
    story.append(Paragraph(
        "<b>The Engineering Fix (Conditional Clamping):</b> If the unconstrained control output exceeds the actuator bounds (<i>u</i><sub>unsat</sub> > <i>u</i><sub>max</sub>) and the error has the same sign (<i>e</i> > 0), integration is frozen. Accumulation resumes only when the system enters the linear region.",
        body_style
    ))

    windup_data = [
        ["Configuration", "Peak Position (m)", "Overshoot Mp (%)", "Settling Time ts (s)", "Max Integral Value (N)", "Hardware Consequence"],
        ["Naive Integration", "1.1290 m", "12.90%", "2.290 s", "+34.55 N (Wound Up)", "Overshoots by 13 cm; motor stays pegged."],
        ["Anti-Windup Clamping", "0.9997 m", "0.00%", "2.225 s", "+19.97 N (Clamped)", "Zero overshoot; immediate linear recovery."],
    ]
    story.append(create_wrapped_table(windup_data, [90, 80, 75, 80, 105, 110]))
    story.append(Spacer(1, 4))

    story.append(add_plot("02_integral_windup.png", width=520, height=270))
    story.append(Paragraph("<i>Figure 8: Actuator saturation and integral windup. Panel 1: Position x(t); Panel 2: Saturated actuator force u(t); Panel 3: Internal integrator term showing wound-up state (34.55 N) vs. clamped state (19.97 N).</i>", meta_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 9: SECTION 7 - PART B (SENSOR NOISE & DERIVATIVE FILTERING)
    # =========================================================================
    story.append(Paragraph("Section 7 (Part B): Sensor Noise (±1 mm) & First-Order Low-Pass Filtering", h1_style))
    story.append(Paragraph(
        "<b>The Real-World Flaw:</b> Encoders and laser rangefinders exhibit measurement noise. We injected &plusmn;1 mm (&plusmn;0.001 m) of uniform sensor jitter &eta;[<i>k</i>] &isin; [-0.001, +0.001] m into position feedback <i>y</i><sub>meas</sub>[<i>k</i>] = <i>x</i>[<i>k</i>] + &eta;[<i>k</i>]. "
        "The discrete derivative depends on the difference between <b>both consecutive samples</b>: &Delta;<i>y</i><sub>meas</sub>[<i>k</i>] = (<i>x</i>[<i>k</i>] - <i>x</i>[<i>k</i>-1]) + (&eta;[<i>k</i>] - &eta;[<i>k</i>-1]). "
        "Because &eta;[<i>k</i>] and &eta;[<i>k</i>-1] fluctuate independently within [-0.001, +0.001] m, their sample-to-sample difference &Delta;&eta; can span up to &plusmn;0.002 m (2 mm). "
        "Dividing by sampling interval &Delta;<i>t</i> = 0.005 s produces discrete pseudo-velocity noise up to:",
        body_style
    ))
    story.append(Paragraph(
        "<i>v</i><sub>noise, max</sub> = (&plusmn;0.002 m) / 0.005 s = <b>&plusmn;0.40 m/s</b>   &implies;   <i>D</i><sub>noise, max</sub> = <i>K</i><sub>d</sub> · <i>v</i><sub>noise, max</sub> = 15 · (&plusmn;0.40) = <b>&plusmn;6.0 N</b>",
        ParagraphStyle("Eq4", parent=body_style, alignment=1, spaceBefore=2, spaceAfter=4, fontName="Helvetica-Bold")
    ))
    story.append(Paragraph(
        "In simulation, this high-frequency differentiation produced peak derivative chatter of 5.799 N (closely matching the theoretical 6.0 N envelope) and actuator force standard deviation of <i>&sigma;</i><sub>u</sub> = 2.544 N, causing severe motor driver heating and mechanical vibration.",
        body_style
    ))
    story.append(Paragraph(
        "<b>The Engineering Fix:</b> We insert a discrete first-order low-pass filter on the derivative term: <i>D</i><sub>filtered</sub>[<i>k</i>] = &alpha; <i>D</i><sub>filtered</sub>[<i>k</i>-1] + (1 - &alpha;) <i>D</i><sub>raw</sub>[<i>k</i>], where &alpha; = <i>&tau;</i><sub>f</sub> / (<i>&tau;</i><sub>f</sub> + &Delta;<i>t</i>) with time constant <i>&tau;</i><sub>f</sub> = 0.03 s (cutoff frequency <i>f</i><sub>c</sub> &approx; 5.3 Hz and <i>&omega;</i><sub>c</sub> &approx; 33.3 rad/s).",
        body_style
    ))

    noise_data = [
        ["Metric (Steady-State t in [2s, 4s])", "Raw Derivative (tau = 0.0 s)", "Filtered Derivative (tau = 0.03 s, fc &approx; 5.3 Hz, &omega;c &approx; 33.3 rad/s)", "Engineering Benefit"],
        ["Actuator Force Std Dev (sigma_u)", "2.544 N", "0.335 N", "86.8% reduction in force chatter"],
        ["Peak Derivative Magnitude (|D|_max)", "5.799 N", "0.762 N", "86.9% reduction in peak derivative noise"],
        ["Physical Hardware Condition", "Continuous buzzing & heating", "Smooth, silent actuation", "Prevents motor driver thermal trip"],
    ]
    story.append(create_wrapped_table(noise_data, [150, 110, 130, 150]))
    story.append(Spacer(1, 4))

    story.append(add_plot("03_sensor_noise_filtering.png", width=520, height=270))
    story.append(Paragraph("<i>Figure 9: Sensor noise (±1 mm) and derivative filtering. Panel 1: Position tracking; Panel 2: Raw vs. filtered derivative chatter; Panel 3: Control force showing 86.8% variance reduction.</i>", meta_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 10: SECTION 7 - PART C (DERIVATIVE KICK ELIMINATION)
    # =========================================================================
    story.append(Paragraph("Section 7 (Part C): Derivative Kick Elimination via Derivative-on-Measurement", h1_style))
    story.append(Paragraph(
        "<b>The Real-World Problem:</b> Textbook PID differentiates tracking error: <i>e</i>(<i>t</i>) = <i>r</i>(<i>t</i>) - <i>y</i>(<i>t</i>). In a digital discrete-time controller with sampling interval &Delta;<i>t</i> = 0.005 s, a sudden 1.0 m step change in setpoint (from 0.0 m to 1.0 m at <i>t</i> = 1.0 s) produces a finite sampled error derivative of &Delta;<i>e</i> / &Delta;<i>t</i> = (1.0 - 0.0) / 0.005 = <b>200.0 m/s</b>. "
        "Multiplying by <i>K</i><sub>d</sub> = 15 N·s/m commands an unconstrained theoretical derivative force of <i>D</i><sub>cmd</sub> = 15 &times; 200.0 = <b>+3000.0 N</b>! "
        "While the actual physical actuator force applied to the cart is limited and clamped to &plusmn;30.0 N, this massive command instantly saturates the motor in a single 5 ms step, causing severe mechanical shock, gear wear, and electrical current surges.",
        body_style
    ))
    story.append(Paragraph(
        "<b>The Engineering Solution (Derivative-on-Measurement):</b> Because reference setpoints are piecewise constant between commands (<i>dr/dt</i> = 0), differentiating error yields <i>de/dt</i> = <i>d(r-y)/dt</i> = -<i>dy/dt</i>. "
        "By evaluating the derivative exclusively on the negative rate of position feedback (-<i>dy/dt</i>), a setpoint step commands <b>zero initial derivative spike</b> (<i>D</i> = 0.0 N at step instant) because cart inertia prevents physical position from changing discontinuously. "
        "Once the cart begins moving, derivative-on-measurement provides identical velocity damping (braking) without derivative kick.",
        body_style
    ))

    kick_data = [
        ["Derivative Formulation", "Theoretical Unconstrained Command", "Actual Applied Actuator Force", "Physical Actuator Impact"],
        ["Derivative on Error (Naive)", "+3000.0 N (Finite Sampled Spike)", "+30.0 N (Saturated in 5 ms)", "Saturates actuator instantly in one step; mechanical stress."],
        ["Derivative on Measurement", "0.0 N (Zero Initial Kick)", "+10.0 N to +30.0 N (Controlled P+I)", "Gentle, progressive actuation; smooth velocity damping."],
    ]
    story.append(create_wrapped_table(kick_data, [125, 125, 125, 165]))
    story.append(Spacer(1, 4))

    story.append(add_plot("04_derivative_kick.png", width=520, height=270))
    story.append(Paragraph("<i>Figure 10: Derivative kick elimination. Panel 1: Position response; Panel 2: Unconstrained derivative term showing +3000 N impulse spike vs. zero kick; Panel 3: Constrained actuator force.</i>", meta_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 11: SECTION 7 - PART D (SAMPLING RATE & DISCRETIZATION LIMITS)
    # =========================================================================
    story.append(Paragraph("Section 7 (Part D): Microcontroller Sampling Rate & Discretization Limits", h1_style))
    story.append(Paragraph(
        "<b>The Physics of Discretization:</b> Digital microcontrollers execute in discrete time steps <i>T</i><sub>s</sub> = 1 / <i>f</i><sub>s</sub>. Between steps, the Digital-to-Analog converter holds the output force constant (Zero-Order Hold, ZOH). A Zero-Order Hold introduces an effective transport delay of <i>T</i><sub>delay</sub> &approx; <i>T</i><sub>s</sub> / 2. This delay adds negative phase lag &Delta;<i>&phi;</i> = -<i>&omega;T</i><sub>s</sub> / 2, which directly erodes the closed-loop phase margin.",
        body_style
    ))
    story.append(Paragraph(
        "We tested the identical tuned PID controller (<i>K</i><sub>p</sub> = 100, <i>K</i><sub>i</sub> = 80, <i>K</i><sub>d</sub> = 15) across six sampling rates from 200 Hz down to 2 Hz interacting with the continuous physical plant:",
        body_style
    ))

    samp_data = [
        ["Sampling Rate (fs)", "Interval (Ts)", "Rise Time tr (s)", "Overshoot Mp (%)", "Settling Time ts (s)", "Closed-Loop Stability Status"],
        ["200 Hz", "5.0 ms", "0.698 s", "0.00%", "2.430 s", "STABLE (Continuous Baseline)"],
        ["50 Hz", "20.0 ms", "0.690 s", "0.00%", "2.367 s", "STABLE (Standard Industrial Loop)"],
        ["20 Hz", "50.0 ms", "0.726 s", "0.00%", "2.448 s", "STABLE (Minor phase lag)"],
        ["10 Hz", "100.0 ms", "0.830 s", "0.00%", "2.561 s", "STABLE (Noticeable latency)"],
        ["5 Hz", "200.0 ms", "0.827 s", "4.51%", "N/A*", "Poorly damped / does not settle within simulation window"],
        ["2 Hz", "500.0 ms", "0.394 s", "21.38%", "N/A*", "Poorly damped / does not settle within simulation window"],
    ]
    story.append(create_wrapped_table(samp_data, [85, 65, 75, 75, 90, 150]))
    story.append(Paragraph("<font size='7'>* N/A: Poorly damped / does not settle within simulation window (&plusmn;2% corridor).</font>", meta_style))

    story.append(add_plot("05_sampling_rate_effects.png", width=520, height=270))
    story.append(Paragraph("<i>Figure 11: Effect of controller sampling frequency (2 Hz to 200 Hz). Top panel shows position trajectory; Bottom panel shows discrete stepped actuator force held by Zero-Order Hold.</i>", meta_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 12: SECTION 8 - PART A (HEURISTIC MANUAL TUNING SEQUENCE)
    # =========================================================================
    story.append(Paragraph("Section 8 (Part A): Systematic Heuristic Manual PID Tuning Workflow", h1_style))
    story.append(Paragraph(
        "When commissioning physical robotic joints or flight actuators on a test bench, control engineers apply a systematic 3-step manual tuning procedure to find balanced gains without risking instability:",
        body_style
    ))
    story.append(Paragraph("• <b>Step 1 (P-Tuning):</b> Zero out <i>K</i><sub>i</sub> and <i>K</i><sub>d</sub>. Gradually increase <i>K</i><sub>p</sub> until the cart moves briskly toward the target. In our plant, increasing <i>K</i><sub>p</sub> to 100 N/m brings the mass to 0.833 m, where it stalls due to spring tension.", bullet_style))
    story.append(Paragraph("• <b>Step 2 (D-Tuning):</b> Introduce <i>K</i><sub>d</sub> to add artificial viscous friction. With <i>K</i><sub>d</sub> = 15 N·s/m, transient velocity is smoothed and deceleration is controlled.", bullet_style))
    story.append(Paragraph("• <b>Step 3 (I-Tuning):</b> Introduce <i>K</i><sub>i</sub> to pull the remaining steady-state offset to zero. Moderate <i>K</i><sub>i</sub> = 80 N/(m·s) provides smooth zero-overshoot convergence in 2.435 s. Excessive <i>K</i><sub>i</sub> = 180 N/(m·s) over-integrates and risks saturation.", bullet_style))

    tune_data = [
        ["Tuning Progression Stage", "Gains (Kp, Ki, Kd)", "Rise Time tr (s)", "Overshoot Mp (%)", "Settling Time ts (s)", "SSE ess (m)", "Observed Dynamics & Behavior"],
        ["Stage 1: P-Only", "(100, 0, 0)", "N/A*", "0.00%", "N/A**", "0.1667 m", "Stalls at 0.833 m due to spring droop; no overshoot."],
        ["Stage 2: PD Dampened", "(100, 0, 15)", "N/A*", "0.00%", "N/A**", "0.1667 m", "Smooth motion, higher damping, persistent steady-state offset."],
        ["Stage 3: Balanced PID", "(100, 80, 15)", "0.695 s", "0.00%", "2.435 s", "0.0013 m", "Optimal: Zero overshoot, fast settling within 2% band."],
        ["Stage 4: Over-Integrated", "(100, 180, 5)", "0.470 s", "0.00%", "1.510 s", "0.0000 m", "Aggressive; sensitive to noise and risks actuator saturation."],
    ]
    story.append(create_wrapped_table(tune_data, [105, 75, 50, 50, 50, 55, 155]))
    story.append(Paragraph("<font size='7'>* N/A: Never reaches 90% setpoint due to steady-state droop. ** N/A: Never enters &plusmn;2% tolerance corridor.</font>", meta_style))

    story.append(add_plot("06_manual_tuning.png", width=520, height=270))
    story.append(Paragraph("<i>Figure 12: Manual tuning sequence showing progressive response changes across the four milestone configurations.</i>", meta_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 13: SECTION 8 - PART B (ZIEGLER-NICHOLS: ASSIGNED PLANT VS. FOPDT)
    # =========================================================================
    story.append(Paragraph("Section 8 (Part B): Ziegler-Nichols Analysis: Assigned Plant G(s)=1/(s+1) vs. Delayed FOPDT Demonstration", h1_style))
    story.append(Paragraph(
        "<b>1. Assigned Ideal Plant G(s) = 1 / (s + 1) — Proof That Pure P-Control Cannot Oscillate:</b><br/>"
        "Modern Monk Labs requested applying the Ziegler-Nichols method to the first-order transfer function <i>G</i>(<i>s</i>) = 1 / (<i>s</i> + 1). "
        "Under ideal continuous proportional feedback (<i>u</i> = <i>K</i><sub>p</sub>(<i>r</i> - <i>y</i>)), the closed-loop transfer function is <i>T</i>(<i>s</i>) = <i>K</i><sub>p</sub> / (<i>s</i> + 1 + <i>K</i><sub>p</sub>), with a single real pole at <i>s</i> = -(1 + <i>K</i><sub>p</sub>). For any finite <i>K</i><sub>p</sub> > 0, this pole stays strictly on the negative real axis, guaranteeing a purely monotonic exponential step response without overshoot or ringing. "
        "In the frequency domain, open-loop phase is &ang;<i>G</i>(<i>j&omega;</i>) = -arctan(<i>&omega;</i>). As frequency <i>&omega;</i> &rarr; &infin;, phase approaches -90&deg;, never reaching the -180&deg; phase crossover required for sustained marginal oscillation (Barkhausen criterion). "
        "Therefore, <b>the assigned ideal continuous plant G(s) = 1/(s+1) has an infinite gain margin and does not possess a finite ultimate gain Ku or ultimate period Pu</b> under pure proportional control.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2. Additional Demonstration: Delayed First-Order-Plus-Dead-Time (FOPDT) System:</b><br/>"
        "To demonstrate the mechanics of the Ziegler-Nichols tuning recipe when oscillations are physically achievable, we introduce an <i>additional delayed system demonstration</i> incorporating a transport dead time of <i>L</i> = 0.2 s: <i>G</i><sub>FOPDT</sub>(<i>s</i>) = <i>e</i><sup>-0.2<i>s</i></sup> / (<i>s</i> + 1). "
        "The delay introduces phase lag -<i>&omega;L</i>, allowing total phase &ang;<i>G</i><sub>FOPDT</sub>(<i>j&omega;</i>) = -arctan(<i>&omega;</i>) - 0.2<i>&omega;</i> to cross -180&deg; at <i>&omega;</i><sub>u</sub> = 8.443 rad/s, yielding a genuine finite ultimate gain <b>Ku = 8.502</b> and ultimate period <b>Pu = 0.744 s</b>.",
        body_style
    ))

    zn_recipe = [
        ["Tuning Methodology", "Identified Parameters", "Kp Formula", "Ti Formula", "Td Formula", "Computed PID Gains (Kp, Ki, Kd)"],
        ["Assigned Plant G(s)=1/(s+1)", "Infinite Gain Margin", "Undefined (Ku=inf)", "Undefined", "Undefined", "Cannot oscillate under pure P-control"],
        ["ZN Ultimate Gain (FOPDT Demo)", "Ku = 8.502, Pu = 0.744 s", "0.60 * Ku", "0.50 * Pu", "0.125 * Pu", "Kp = 5.101, Ki = 13.711, Kd = 0.475"],
        ["ZN Reaction Curve (FOPDT Demo)", "K=1.0, L=0.2s, tau=1.0s", "1.2*(tau/(K*L))", "2.0 * L", "0.50 * L", "Kp = 6.000, Ki = 15.000, Kd = 0.600"],
        ["Refined Manual PID (FOPDT Demo)", "Damped / Low Overshoot", "User Chosen", "User Chosen", "User Chosen", "Kp = 3.000, Ki = 4.000, Kd = 0.350"],
    ]
    story.append(create_wrapped_table(zn_recipe, [115, 105, 60, 50, 50, 160]))
    story.append(Spacer(1, 3))

    story.append(add_plot("07_ziegler_nichols.png", width=520, height=255))
    story.append(Paragraph("<i>Figure 13: Ziegler-Nichols analysis. Panel A: Assigned continuous G(s)=1/(s+1) monotonic response (no finite Ku); Panel B: Additional delayed FOPDT system (L=0.2s) reaching sustained oscillation at Ku=8.50, Pu=0.74s; Panel C: Reaction curve identification; Panel D: Closed-loop comparison on the delayed system.</i>", meta_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 14: SECTION 9 (REUSABLE PRODUCTION CODE ARCHITECTURE)
    # =========================================================================
    story.append(Paragraph("Section 9: Reusable Production PID Architecture & Guardrails", h1_style))
    story.append(Paragraph(
        "All defensive features developed in this project have been consolidated into a modular, production-ready Python class in <code>src/controller.py</code>. Below is the verified algorithmic implementation with full indentation and structural formatting:",
        body_style
    ))

    code_snippet = (
        "class PIDController:\n"
        "    def __init__(self, kp: float = 0.0, ki: float = 0.0, kd: float = 0.0,\n"
        "                 output_limits: tuple[float, float] = (-30.0, 30.0),\n"
        "                 filter_tau: float = 0.0, derivative_on_measurement: bool = True,\n"
        "                 anti_windup: bool = True) -> None:\n"
        "        if kp < 0.0 or ki < 0.0 or kd < 0.0:\n"
        "            raise ValueError(f'Gains must be non-negative. Got kp={kp}, ki={ki}, kd={kd}.')\n"
        "        u_min, u_max = output_limits\n"
        "        if u_min >= u_max:\n"
        "            raise ValueError(f'Minimum limit ({u_min}) must be strictly less than maximum ({u_max}).')\n"
        "        if filter_tau < 0.0:\n"
        "            raise ValueError(f'Filter time constant filter_tau must be >= 0. Got {filter_tau}.')\n"
        "        self.kp, self.ki, self.kd = float(kp), float(ki), float(kd)\n"
        "        self.u_min, self.u_max = float(u_min), float(u_max)\n"
        "        self.filter_tau = float(filter_tau)\n"
        "        self.derivative_on_measurement = bool(derivative_on_measurement)\n"
        "        self.anti_windup = bool(anti_windup)\n"
        "        self.reset()\n\n"
        "    def reset(self) -> None:\n"
        "        self.integral = 0.0\n"
        "        self.prev_error, self.prev_measurement = None, None\n"
        "        self.filtered_derivative, self.last_output = 0.0, 0.0\n\n"
        "    def update(self, setpoint: float, measurement: float, dt: float) -> float:\n"
        "        if dt <= 0.0:\n"
        "            raise ValueError(f'Time step dt must be strictly positive (> 0), got {dt} s.')\n"
        "        error = float(setpoint) - float(measurement)\n"
        "        p_term = self.kp * error\n\n"
        "        # Derivative-on-Measurement & First-Order Low-Pass Filter\n"
        "        if self.derivative_on_measurement:\n"
        "            raw_derivative = 0.0 if self.prev_measurement is None else -(float(measurement) - self.prev_measurement) / dt\n"
        "        else:\n"
        "            raw_derivative = 0.0 if self.prev_error is None else (error - self.prev_error) / dt\n"
        "        if self.filter_tau > 0.0:\n"
        "            alpha = self.filter_tau / (self.filter_tau + dt)\n"
        "            self.filtered_derivative = (alpha * self.filtered_derivative) + ((1.0 - alpha) * raw_derivative)\n"
        "            derivative_value = self.filtered_derivative\n"
        "        else:\n"
        "            self.filtered_derivative = raw_derivative\n"
        "            derivative_value = raw_derivative\n"
        "        d_term = self.kd * derivative_value\n\n"
        "        # Integral Term & Anti-Windup Clamping\n"
        "        delta_integral = self.ki * error * dt\n"
        "        tentative_integral = self.integral + delta_integral\n"
        "        unconstrained_output = p_term + tentative_integral + d_term\n"
        "        if self.anti_windup:\n"
        "            pushing_positive = (unconstrained_output > self.u_max) and (error > 0.0)\n"
        "            pushing_negative = (unconstrained_output < self.u_min) and (error < 0.0)\n"
        "            if pushing_positive or pushing_negative:\n"
        "                i_term = self.integral\n"
        "            else:\n"
        "                self.integral = max(self.u_min, min(tentative_integral, self.u_max))\n"
        "                i_term = self.integral\n"
        "        else:\n"
        "            self.integral = tentative_integral\n"
        "            i_term = self.integral\n\n"
        "        u_unconstrained = p_term + i_term + d_term\n"
        "        u_saturated = max(self.u_min, min(u_unconstrained, self.u_max))\n"
        "        self.prev_error = error\n"
        "        self.prev_measurement = float(measurement)\n"
        "        return u_saturated"
    )

    p_code = Preformatted(code_snippet, code_block_style)
    t_code = Table([[p_code]], colWidths=[540])
    t_code.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f7f9")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#b8cddc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_code)

    story.append(Spacer(1, 4))
    story.append(Paragraph("Verification Across 22 Automated Unit Tests", h2_style))
    story.append(Paragraph(
        "The codebase contains 22 automated test functions in the <code>tests/</code> directory verifying plant energy conservation, analytical steady-state formulas, derivative kick elimination, anti-windup clamping, and metrics calculations. The project uses NumPy and Matplotlib as external dependencies for simulation and plotting; only Python's <code>unittest</code> runner is built in.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 15: SECTION 10, ROBOTICS APPLICATIONS, MYTHS, AI DISCLOSURE & CONCLUSION
    # =========================================================================
    story.append(Paragraph("Section 10: Robotics Applications, PID Myths Corrected & Disclosures", h1_style))

    story.append(Paragraph("Four Real-World Robotics Applications of PID", h2_style))
    story.append(Paragraph("1. <b>Differential-Drive Mobile Robots (AMRs):</b> Independent wheel velocity PID loops enforce matched RPMs to ensure straight-line tracking and exact rotational heading.", bullet_style))
    story.append(Paragraph("2. <b>Quadrotor UAV Flight Controllers:</b> Cascaded nested loops: high-speed inner rate PID (500 Hz) stabilizes angular body rates (<i>P</i>, <i>Q</i>, <i>R</i>), while outer attitude PID (100 Hz) regulates pitch/roll angles.", bullet_style))
    story.append(Paragraph("3. <b>Robotic Manipulator Arm Joints:</b> PD controllers combined with feedforward gravity cancellation model joint compliance and accurate pick-and-place positioning.", bullet_style))
    story.append(Paragraph("4. <b>Surgical Robot Force Feedback (Haptics):</b> Fast force-controlled PID loops maintain compliant, delicate contact forces against soft biological tissues without tissue damage.", bullet_style))

    story.append(Paragraph("Four Common PID Myths Debunked by Control Engineering", h2_style))
    story.append(Paragraph("• <i>Myth 1: 'PID is just pure math and works identically on all physical systems.'</i><br/><b>Correction:</b> Real actuators saturate, sensors jitter, and mechanics have backlash. Naive PID fails on hardware without anti-windup and filters.", bullet_style))
    story.append(Paragraph("• <i>Myth 2: 'More integral gain (Ki) is always better if you have steady-state error.'</i><br/><b>Correction:</b> High <i>K</i><sub>i</sub> erodes phase margin, introduces severe overshoot, and triggers destructive integral windup.", bullet_style))
    story.append(Paragraph("• <i>Myth 3: 'Derivative control must always differentiate tracking error.'</i><br/><b>Correction:</b> Differentiating error can produce a very large finite derivative kick in a sampled digital controller when the setpoint changes abruptly. Derivative-on-measurement avoids this setpoint kick.", bullet_style))
    story.append(Paragraph("• <i>Myth 4: 'Ziegler-Nichols tuning provides optimal gains for modern robotics.'</i><br/><b>Correction:</b> Classic Z-N aims for a 25% quarter-decay ratio, resulting in 50%+ overshoot. Modern robotics requires conservative detuning.", bullet_style))

    story.append(Paragraph("Honest AI Assistance & Academic Integrity Disclosure", h2_style))
    story.append(Paragraph(
        "Antigravity AI was used extensively to generate and organize the Python implementation, experiment scripts, plots, and draft report. The candidate did not independently author or audit every component. The included automated tests and experiment scripts were rerun in a Python execution environment as part of a separate software review. These checks demonstrate software and simulation execution only and are not a substitute for independent engineering review or validation on physical hardware. The candidate is reviewing the implementation, assumptions, and limitations before technical evaluation.",
        body_style
    ))

    story.append(Paragraph("Conclusion", h2_style))
    story.append(Paragraph(
        "This project successfully bridged theoretical control equations with real-world Physical AI engineering constraints. By combining analytical derivations with empirical simulations, we demonstrated why pure proportional control stops short (<i>x</i><sub>ss</sub> = <i>K</i><sub>p</sub> / (<i>K</i><sub>p</sub> + <i>k</i>)), why 20 N is mandatory at equilibrium, and how defensive engineering (anti-windup, derivative-on-measurement, low-pass filtering, and adequate sampling rates) transforms naive textbook mathematics into resilient, production-grade robotics software.",
        body_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Technical PDF generated successfully at: {filename}")


if __name__ == "__main__":
    report_dir = os.path.abspath(os.path.dirname(__file__))
    plots_dir = os.path.abspath(os.path.join(report_dir, "..", "plots"))
    output_pdf = os.path.join(report_dir, "technical_report.pdf")
    build_pdf(output_pdf, plots_dir)
