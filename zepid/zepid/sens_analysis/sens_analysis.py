import warnings
import math 
import numpy as np
import pandas as pd
from scipy.stats import norm
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.genmod.families import family
from statsmodels.genmod.families import links
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


def rr_corr(rr_obs,rr_conf,p1,p0):
    '''Simple Sensitivity analysis calculator for Risk Ratios. Estimates the impact of 
    an unmeasured confounder on the results of a conducted study. Observed RR comes from 
    the data analysis, while the RR between the unmeasured confounder and the outcome should
    be obtained from prior literature or constitute an reasonable guess. Probability of exposure
    between the groups should also be reasonable numbers. This function can be adapted to be part
    of a sensitivity analysis with repeated sampling of rr_conf, p1, and p0 from set distributions
    to obtain a range of effects. 
    
    See online example for further example of this analysis. A 
    created function for the repeated sampling is not available for this since the type of 
    distribution and values to include as reasonable should be careully considered by the researcher.
    To encourage careful thought, a function for this analysis has not been created, but examples of 
    the implementation are available to help researchers create their own. 
    
    rr_obs:
        -Observed RR from the data
    rr_conf:
        -Value of RR between unmeasured confounder and the outcome of interest
    p1:
        -Estimated proportion of those with unmeasured confounder in the exposed group
    p0:
        -Estimated porportion of those with unmeasured confounder in the unexposed group
    '''
    denom = (p1*(rr_conf-1)+1) / (p0*(rr_conf-1)+1)
    rr_adj = rr_obs / denom
    return rr_adj
        

def delta_beta(df,eq,beta,model='glm',match='',family=sm.families.family.Binomial(sm.families.links.logit),group=False,groupvar=''):
    '''Delta-beta is a sensitivity analysis that tracks the change in the beta estimate(s) of interest 
    when a single observation is excluded from the dataframe for all the observations. This function 
    uses statsmodels to calculate betas. All observations and the difference in estimates is stored 
    in a pandas dataframe that is returned by the function. Multiple delta betas are able to estimated
    at once. All beta(s) of interest should be included in a list. Difference in estimates is calculated 
    by substracting the full model results from the reduced results

    NOTE: that if a delta beta is missing in the returned dataframe, this indicates the model had convergence
    issues when that observation (or group of observations) was removed from the model.
    
    Currently supported model options include:
        -Generalized linear model
        -Generalized estimation equations
    
    df:
        -Dataframe of observations to use for delta beta analysis
    eq:
        -Regression model formula
    beta:
        -Which beta's are of interest. Single string (variable name) or a list of strings that designate
         variable names of beta(s) of interest
    model:
        -Whether to use GLM or GEE. Default is GLM
    group:
        -Whether to drop groups. Default is False, which drops individual observations rather than by 
         dropping groups of observations. If group is set to True, groupvar must be specified
    groupvar:
        -Variable which to group by to conduct the delta beta analysis. group must be set to True for this variable to be used.
        
    Return: dataframe of requested betas in a pandas dataframe
    '''
    if type(beta) is not list:
        raise ValueError("Input 'beta' must be a list object")
    if model=='glm':
        fmodel = smf.glm(eq,df,family=family).fit()
    elif model=='gee':
        if match == '':
            raise ValueError('Please specify matching variable for GEE')
        else:
            fmodel = smf.gee(eq,df,match,family=family).fit()
    else:
        raise ValueError('Please specify a supported model')
    dbr = {}
    if group == False:
        for i in range(len(df)):
            dfs = df.drop(df.index[i])
            try:
                if model=='glm':
                    rmodel = smf.glm(eq,dfs,family=family).fit()
                elif model=='gee':
                    rmodel = smf.gee(eq,dfs,match,family=family).fit()
                for b in beta:
                    dbr.setdefault(b,[]).append(rmodel.params[b])
            except:
                for b in beta:
                    dbr.setdefault(b,[]).append(np.nan)
        rf = pd.DataFrame.from_dict(dbr)
    if group == True:
        if groupvar == '':
            raise ValueError('Must specify group variable to drop observations by')
        for i in list(df[groupvar].unique()):
            dfs = df[df[groupvar]!=i]
            try:
                if model=='glm':
                    rmodel = smf.glm(eq,dfs,family=family).fit()
                elif model=='gee':
                    rmodel = smf.gee(eq,dfs,match,family=family).fit()
                for b in beta:
                    dbr.setdefault(b,[]).append(rmodel.params[b])
            except:
                for b in beta:
                    dbr.setdefault(b,[]).append(np.nan)
        rf = pd.DataFrame.from_dict(dbr)
    for b in beta:
        rf[b] -= fmodel.params[b]
    return rf


def e_value(effect_measure,lcl,ucl,measure='RR',rare=False,null=1,decimal=2):
    '''Calculates the E-value, based on calculations provided by VanderWeele & Ding (2017). 
    The e-value assesses the robustness of observational findings to potential unmeasured 
    confounders. The farther E is from 1, the stronger the unmeasure confounding would need 
    to be to nullify the results. For a full discussion and the formulas used to calculate, 
    see "Sensitivity Analysis in Observational Research: Introdcuing the E-Value" in 
    Annals of Internal Medicine 2017;167:268-274
    
    Note on approximations:
        -The approximation for the odds ratio works best when the outcome probabilities are 
         between 0.2 to 0.8, but will work for 0.1 to 0.9
    
    effect_measure:
        -The point estimate of the measure of interest. Must be integer or float
    lcl:
        -Lower confidence limit of the measure of interest. Must be integer or float
    ucl:
        -Upper confidence limit of the measure of interst. Must be integer or float
    measure:
        -Effect measure used in study. Default is the Relative Risk
              Measure         Keywork
            Relative Risk       'RR'
            Odds Ratio          'OR'
            Hazard Ratio        'HR'
            Rate Ratio          'Rate'
    rare:
        -Whether the rare disease outcome (<15%) is met. When False, the approximation method
         is used for Odds Ratio and Hazard Ratio. The option for rare does not impact the other
         effect measures. The default is set to False
    null:
        -Which reference value to compare the magnitude of unmeasured confounding required to 
         shift the estimate. Default is set to 1 (the null value).
    decimal:
        -Number of decimal places to display
    '''
    if ((measure=='OR')|(measure=='HR')):
        print('\nWARNING: if the outcome is common, OR/HR need to use the approximation method\nfor the E-value. The approximation method is implemented by default. If the\noutcome is relatively rare (<15%) then the approximation is not required')
    if ((measure=='RR') | (((measure=='OR')|(measure=='HR'))&(rare==True)) | (measure=='Rate')):
        m = effect_measure / null
        l = lcl / null
        u = ucl / null
    if ((measure=='OR') & (rare==False)):
        m = math.sqrt(effect_measure) / null
        l = math.sqrt(lcl) / null
        u = math.sqrt(ucl) / null
    if ((measure=='HR')&(rare==False)):
        m = (1 - 0.5**(math.sqrt(effect_measure))) / (1 - 0.5**(math.sqrt((1/effect_measure)))) / null
        l = (1 - 0.5**(math.sqrt(lcl))) / (1 - 0.5**(math.sqrt((1/lcl)))) / null 
        u = (1 - 0.5**(math.sqrt(ucl))) / (1 - 0.5**(math.sqrt((1/ucl)))) / null 
    #calculate e-value for RR>1
    if m >= null:
        evalue = m + math.sqrt((m * (m-1)))
        if l > null:
            evalue_cl = l + math.sqrt((l * (l-1)))
        else:
            evalue_cl = 1
    #calculate e-value for RR<1
    if m < null:
        mi = 1 / m
        evalue = mi + math.sqrt((mi * (mi-1)))
        if u < null:
            ui = 1 / u
            evalue_cl = ui + math.sqrt((ui * (ui-1)))
        else:
            evalue_cl = 1
    print('----------------------------------------------------------------------')
    print('Effect Measure: '+measure+'\t(Reference = '+str(null)+')\n\nE-values\n\tPoint Estimate = \t'+str(round(evalue,decimal)))
    print('\tConfidence Limit = \t'+str(round(evalue_cl,decimal)))
    print('----------------------------------------------------------------------')


def e_value_difference(stand_effect_size,se,null=1,decimal=2):
    '''Calculates the E-value, based on calculations provided by VanderWeele & Ding (2017).
    This function implements the E-value calculation for differences is continuous outcomes.
    It utilizes an approximation method discussed in the introduction article. The e-value 
    assesses the robustness of observational findings to potential unmeasured confounders. 
    The farther E is from 1, the stronger the unmeasure confounding would need to be to 
    nullify the results. For a full discussion and the formulas used to calculate, see 
    "Sensitivity Analysis in Observational Research: Introdcuing the E-Value" in 
    Annals of Internal Medicine 2017;167:268-274
    
    stand_effect_size:
        -The standard effect size (mean of the outcome variable divided by SD of the outcome)
    se:
        -Standard error of the standard effect size
    null:
        -Which reference value to compare the magnitude of unmeasured confounding required to 
         shift the estimate. Default is set to 1 (the null value)
    decimal:
        -Number of decimal places to display
    '''
    m = math.exp(0.91*stand_effect_size) / null
    l = math.exp((0.91*stand_effect_size) - (1.78*se)) / null
    u = math.exp((0.91*stand_effect_size) + (1.78*se)) / null 
    if m >= null:
        evalue = m + math.sqrt((m * (m-1)))
        if l > null:
            evalue_cl = lcl + math.sqrt((lcl * (lcl-1)))
        else:
            evalue_cl = 1
    if m < null:
        mi = 1 / m
        evalue = mi + math.sqrt((mi * (mi-1)))
        if u < null:
            ui = 1 / u
            evalue_cl = ui + math.sqrt((ui * (ui-1)))
        else:
            evalue_cl = 1
    print('----------------------------------------------------------------------')
    print('Effect Measure: Difference in continuous outcomes \t(Reference = '+str(null)+')\n\nE-values\n\tPoint Estimate = \t'+str(round(evalue,decimal)))
    print('\tConfidence Limit = \t'+str(round(evalue_cl,decimal)))
    print('----------------------------------------------------------------------')


def e_value_RD(N,f,p1,se1,p0,se0,null=0,alpha=0.05,decimal=2):
    '''Calculates the E-value, based on calculations provided by VanderWeele & Ding (2017).
    This function implements the E-value calculation for risk difference.
    
    The e-value 
    assesses the robustness of observational findings to potential unmeasured confounders. 
    The farther E is from 1, the stronger the unmeasure confounding would need to be to 
    nullify the results. For a full discussion and the formulas used to calculate, see 
    "Sensitivity Analysis in Observational Research: Introdcuing the E-Value" in 
    Annals of Internal Medicine 2017;167:268-274
    
    N:
        -total number of subjects
    f:
        -proportion of individuals that are exposed
    p1:
        -Adjusted risk in the exposed
    se1:
        -Standard error of the risk in the exposed
    p0:
        -Adjusted risk in the unexposed
    se2:
        -Standard error of the risk in the unexposed
    null:
        -Which reference value to compare the magnitude of unmeasured confounding required to 
         shift the estimate. Default is set to 0 (the null value)
    alpha:
        -Significance level for two-sided confidence intervals. Default is 0.05
    decimal:
        -Number of decimal places to display. Default is 2
    '''
    if p1 < p0:
        raise ValueError('Please choose the reference category so that the RD > 0')
    sf = f * (1 - f)/N
    s1_2 = se1**2
    s0_2 = se0**2
    diff = (p0*(1-f)) - (p1*f)
    m = (math.sqrt(((null+diff)**2) + (4*p1*p0*f*(1-f))) - (null+diff)) / (2*p0*f)
    if (null <= m):
        evalue =  m + math.sqrt((m * (m-1)))
    else:
        mi = 1 / m
        evalue = mi + math.sqrt((mi * (mi-1)))
    if (p1 - p0 <= null):
        raise ValueError('For the risk difference calculation, the null value must be greater than or equal to the point estimate')
    zalpha = norm.ppf((1-alpha/2),loc=0,scale=1)
    lcl = p1 - p0 - (zalpha * math.sqrt(s1_2 + s0_2))
    if (lcl <= null):
        evalue_cl = 1
    else:
        search = list(np.arange(1,m,0.0001))
        RDsearch = [p1 - p0 * s for s in search]
        fsearch = [f + ((1-f)/s) for s in search]
        lowsearch = [(r*f) - zalpha * math.sqrt((s1_2 + s0_2*(s**2))*(f**2) + (r**2)*((1-1/s)**2)*sf) for s,r,f in zip(search,RDsearch,fsearch)]
        lind = [v <= null for v in lowsearch]
        first = lind.index(True)
        l = search[first]
        if l >= null:
            evalue_cl =  l + math.sqrt((l * (l-1)))
        else:
            li = 1 / l
            evalue_cl = li + math.sqrt((li * (li-1)))
    print('----------------------------------------------------------------------')
    print('Effect Measure: Risk Difference \t(Reference = '+str(null)+')\n\nE-values\n\tPoint Estimate = \t'+str(round(evalue,decimal)))
    print('\tConfidence Limit = \t'+str(round(evalue_cl,decimal)))
    print('----------------------------------------------------------------------')

