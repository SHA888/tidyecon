"""
validate/fixtures.py
====================
Hardcoded numerical benchmarks derived from R (broom + modelsummary)
and Stata.  These serve as the ground truth for regression tests.

Sources
-------
R fixtures : produced with R 4.4.1, broom 1.0.6, stats 4.4.1
Stata fixtures : Stata 18, standard datasets

To regenerate from R:
    library(broom); library(datasets)
    fit <- lm(mpg ~ hp + wt, data = mtcars)
    print(tidy(fit), digits = 10)
    print(glance(fit), digits = 10)
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CoefFixture:
    term: str
    estimate: float
    std_error: float
    statistic: float
    p_value: float
    conf_low_95: float
    conf_high_95: float


@dataclass
class GlanceFixture:
    nobs: int
    r_squared: float
    adj_r_squared: float
    f_statistic: float | None = None


@dataclass
class ModelFixture:
    name: str
    description: str
    source: str  # e.g. "R 4.4.1 lm()"
    model_factory: str  # human description of how to build the model
    coefs: list[CoefFixture] = field(default_factory=list)
    glance: GlanceFixture | None = None
    tol_coef: float = 1e-5
    tol_se: float = 1e-5
    tol_r2: float = 1e-6


# ── R benchmark: OLS mpg ~ hp + wt (mtcars, n=32) ────────────────────────────
_MTCARS_INLINE = """
mpg,cyl,hp,wt,am
21.0,6,110,2.620,1
21.0,6,110,2.875,1
22.8,4,93,2.320,1
21.4,6,110,3.215,0
18.7,8,175,3.440,0
18.1,6,105,3.460,0
14.3,8,245,3.570,0
24.4,4,62,3.190,0
22.8,4,95,3.150,0
19.2,6,123,3.440,0
17.8,6,123,3.440,0
16.4,8,180,4.070,0
17.3,8,180,3.730,0
15.2,8,180,3.780,0
10.4,8,205,5.250,0
10.4,8,215,5.424,0
14.7,8,230,5.345,0
32.4,4,66,2.200,1
30.4,4,52,1.615,1
33.9,4,65,1.835,1
21.5,6,97,2.465,0
15.5,8,150,3.520,0
15.2,8,150,3.435,0
13.3,8,245,3.840,0
19.2,6,175,3.845,0
27.3,4,66,1.935,1
26.0,4,91,2.140,1
30.4,4,113,1.513,1
15.8,8,264,3.170,1
19.7,6,175,2.770,1
15.0,8,335,3.570,1
21.4,4,109,2.780,1
""".strip()

_MTCARS_FACTORY_PREAMBLE = (
    "import io, pandas as pd, statsmodels.api as sm\n"
    f"mtcars = pd.read_csv(io.StringIO({_MTCARS_INLINE!r}))\n"
)

OLS_MTCARS = ModelFixture(
    name="ols_mtcars_hp_wt",
    description="OLS: mpg ~ hp + wt, mtcars dataset (n=32)",
    source="R 4.4.1  lm(mpg ~ hp + wt, data = mtcars)",
    model_factory=(
        _MTCARS_FACTORY_PREAMBLE + "X = sm.add_constant(mtcars[['hp', 'wt']])\n"
        "model = sm.OLS(mtcars['mpg'], X).fit()"
    ),
    # 95% CIs computed as estimate ± qt(0.975, df=29) * std_error,
    # which matches R's confint(lm(...)) to machine precision.
    coefs=[
        CoefFixture("const", 37.22727012, 1.59878754, 23.2847964, 2.565e-20, 33.957342, 40.497199),
        CoefFixture("hp", -0.03177295, 0.00902971, -3.5190399, 1.782e-03, -0.050240, -0.013305),
        CoefFixture("wt", -3.87783074, 0.63273151, -6.1290048, 1.126e-06, -5.171935, -2.583727),
    ],
    glance=GlanceFixture(nobs=32, r_squared=0.82680, adj_r_squared=0.81484, f_statistic=69.211),
    tol_coef=1e-4,
    tol_se=1e-4,
)

# ── R benchmark: Logit am ~ hp + wt (mtcars, n=32) ───────────────────────────
LOGIT_MTCARS = ModelFixture(
    name="logit_mtcars_hp_wt",
    description="Logit: am ~ hp + wt, mtcars dataset (n=32)",
    source="R 4.4.1  glm(am ~ hp + wt, data = mtcars, family = binomial)",
    model_factory=(
        _MTCARS_FACTORY_PREAMBLE + "X = sm.add_constant(mtcars[['hp', 'wt']])\n"
        "model = sm.Logit(mtcars['am'], X).fit(disp=False)"
    ),
    coefs=[
        CoefFixture("const", 18.86630, 7.44356, 2.5348, 0.01126, 4.277, 33.456),
        CoefFixture("hp", 0.03626, 0.01778, 2.0394, 0.04142, 0.001, 0.071),
        CoefFixture("wt", -8.08348, 3.06868, -2.6341, 0.00845, -14.098, -2.069),
    ],
    glance=GlanceFixture(nobs=32, r_squared=float("nan"), adj_r_squared=float("nan")),
    tol_coef=1e-3,
    tol_se=1e-3,
)

# ── pyfixest benchmark: feols mpg ~ hp | cyl (mtcars, n=32) ───────────────────
FEOLS_MTCARS = ModelFixture(
    name="feols_mtcars_hp_cyl",
    description="Feols: mpg ~ hp | cyl, mtcars dataset (n=32)",
    source="R 4.4.1  fixest::feols(mpg ~ hp | cyl, data = mtcars)",
    model_factory=(
        _MTCARS_FACTORY_PREAMBLE + "import pyfixest as pf\n"
        "model = pf.feols('mpg ~ hp | cyl', data=mtcars)"
    ),
    coefs=[
        CoefFixture("hp", -0.019439, 0.014048, -1.383767, 0.177363, -0.048214, 0.009337),
    ],
    glance=GlanceFixture(nobs=32, r_squared=0.786336, adj_r_squared=0.763444, f_statistic=None),
    tol_coef=1e-4,
    tol_se=1e-4,
)


# ── All fixtures ──────────────────────────────────────────────────────────────
ALL_FIXTURES: list[ModelFixture] = [
    OLS_MTCARS,
    LOGIT_MTCARS,
    FEOLS_MTCARS,
]
