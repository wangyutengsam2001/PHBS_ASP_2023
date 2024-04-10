# -*- coding: utf-8 -*-
"""
Created on Tue Sep 19 22:56:58 2017

@author: jaehyuk
"""
import numpy as np
import scipy.stats as ss
import pyfeng as pf

def basket_check_args(spot, vol, corr_m, weights):
    '''
    This function simply checks that the size of the vector (matrix) are consistent
    '''
    n = spot.size
    assert( n == vol.size )
    assert( corr_m.shape == (n, n) )
    return None
    
def basket_price_mc_cv(
    strike, spot, vol, weights, texp, cor_m, 
    intr=0.0, divr=0.0, cp=1, n_samples=10000
):
    # price1 = MC based on BSM
    rand_st = np.random.get_state() # Store random state first
    price1 = basket_price_mc(
        strike, spot, vol, weights, texp, cor_m,
        intr, divr, cp, True, n_samples)
    
    ''' 
    compute price2: mc price based on normal model
    make sure you use the same seed

    # Restore the state in order to generate the same state
    np.random.set_state(rand_st)  
    price2 = basket_price_mc(
        strike, spot, spot*vol, weights, texp, cor_m,
        intr, divr, cp, False, n_samples)
    '''
    np.random.set_state(rand_st)  
    price2 = basket_price_mc(
        strike, spot, spot*vol, weights, texp, cor_m,
        intr, divr, cp, False, n_samples)

    ''' 
    compute price3: analytic price based on normal model
    
    price3 = basket_price_norm_analytic(
        strike, spot, vol, weights, texp, cor_m, intr, divr, cp)
    '''
    price3 = basket_price_norm_analytic(
        strike, spot, spot*vol, weights, texp, cor_m, intr, divr, cp
    )
    
    # return two prices: without and with CV
    return np.array([price1, price1 + (price3 - price2)])


def basket_price_mc(
    strike, spot, vol, weights, texp, cor_m,
    intr=0.0, divr=0.0, cp=1, bsm=True, n_samples = 100000
):
    basket_check_args(spot, vol, cor_m, weights)
    
    div_fac = np.exp(-texp*divr)
    disc_fac = np.exp(-texp*intr)
    forward = spot / disc_fac * div_fac

    cov_m = vol * cor_m * vol[:,None]
    chol_m = np.linalg.cholesky(cov_m)  # L matrix in slides

    n_assets = spot.size
    znorm_m = np.random.normal(size=(n_assets, n_samples))
    
    if( bsm ) :
        # Black-Scholes Model
        prices = np.zeros_like(znorm_m)
        for k in range(n_assets):        
            prices[k] = forward[k] * np.exp(-0.5 * texp * cov_m[k, k] + np.sqrt(texp) * chol_m[k,:] @ znorm_m)

    else:
        # bsm = False: normal model
        prices = forward[:,None] + np.sqrt(texp) * chol_m @ znorm_m
    
    price_weighted = weights @ prices
    
    price = np.mean( np.fmax(cp*(price_weighted - strike), 0) )
    return disc_fac * price


def basket_price_norm_analytic(
    strike, spot, vol, weights, 
    texp, cor_m, intr=0.0, divr=0.0, cp=1
):
    # 1. compute the forward of the basket
    div_fac = np.exp(-texp*divr)
    disc_fac = np.exp(-texp*intr)
    forward = spot / disc_fac * div_fac

    # 2. compute the normal volatility of basket
    cov_m = vol * cor_m * vol[:,None]
    if np.sum(weights) == 1: # basket option
        sigma = np.sqrt(weights @ cov_m @ weights[:,None])
    if (np.sum(weights) == 0) & (len(weights) == 2): # spread option
        sigma_N1 = forward[0] * np.sqrt(cov_m[0, 0])
        sigma_N2 = forward[1] * np.sqrt(cov_m[1, 1])
        rou = cov_m[0, 1] / np.sqrt(cov_m[0, 0] * cov_m[1, 1])
        sigma = np.sqrt(sigma_N1 ** 2 + sigma_N2 ** 2 - 2 * rou * sigma_N1 * sigma_N2)

    # 3. plug in the forward and volatility to the normal price formula
    norm = pf.Norm(sigma, intr=intr, divr=divr)
    prices = norm.price(strike, spot, texp, cp=cp)
    price = weights @ prices

    return price
