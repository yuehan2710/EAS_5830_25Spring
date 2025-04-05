// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/AccessControl.sol"; //This allows role-based access control through _grantRole() and the modifier onlyRole
import "@openzeppelin/contracts/token/ERC20/ERC20.sol"; //This contract needs to interact with ERC20 tokens

contract AMM is AccessControl{
    bytes32 public constant LP_ROLE = keccak256("LP_ROLE");
	uint256 public invariant;
	address public tokenA;
	address public tokenB;
	uint256 feebps = 3; //The fee in basis points (i.e., the fee should be feebps/10000)

	event Swap( address indexed _inToken, address indexed _outToken, uint256 inAmt, uint256 outAmt );
	event LiquidityProvision( address indexed _from, uint256 AQty, uint256 BQty );
	event Withdrawal( address indexed _from, address indexed recipient, uint256 AQty, uint256 BQty );

	/*
		Constructor sets the addresses of the two tokens
	*/
    constructor( address _tokenA, address _tokenB ) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender );
        _grantRole(LP_ROLE, msg.sender);

		require( _tokenA != address(0), 'Token address cannot be 0' );
		require( _tokenB != address(0), 'Token address cannot be 0' );
		require( _tokenA != _tokenB, 'Tokens cannot be the same' );
		tokenA = _tokenA;
		tokenB = _tokenB;

    }


	function getTokenAddress( uint256 index ) public view returns(address) {
		require( index < 2, 'Only two tokens' );
		if( index == 0 ) {
			return tokenA;
		} else {
			return tokenB;
		}
	}

	/*
		The main trading functions
		
		User provides sellToken and sellAmount

		The contract must calculate buyAmount using the formula:
	*/
	function tradeTokens( address sellToken, uint256 sellAmount ) public {
		require( invariant > 0, 'Invariant must be nonzero' );
		require( sellToken == tokenA || sellToken == tokenB, 'Invalid token' );
		require( sellAmount > 0, 'Cannot trade 0' );
		require( invariant > 0, 'No liquidity' );
		uint256 qtyA;
		uint256 qtyB;
		uint256 swapAmt;

		//YOUR CODE HERE 

    address buyToken = (sellToken == tokenA) ? tokenB : tokenA;

    uint256 reserveSell = ERC20(sellToken).balanceOf(address(this));
    uint256 reserveBuy = ERC20(buyToken).balanceOf(address(this));

    // Pull the token from the trader
    require(
        ERC20(sellToken).transferFrom(msg.sender, address(this), sellAmount),
        "Transfer failed"
    );

    // Apply fee (feebps is in basis points, so divide by 10,000)
    uint256 amountInWithFee = (sellAmount * (10000 - feebps)) / 10000;

    // Use Uniswap constant product formula: Δy = (y * Δx) / (x + Δx)
    uint256 amountOut = (reserveBuy * amountInWithFee) / (reserveSell + amountInWithFee);

    require(amountOut > 0, "Insufficient output");

    // Transfer buy token to user
    require(
        ERC20(buyToken).transfer(msg.sender, amountOut),
        "Output transfer failed"
    );

    emit Swap(sellToken, buyToken, sellAmount, amountOut);


		uint256 new_invariant = ERC20(tokenA).balanceOf(address(this))*ERC20(tokenB).balanceOf(address(this));
		require( new_invariant >= invariant, 'Bad trade' );
		invariant = new_invariant;
	}

	/*
		Use the ERC20 transferFrom to "pull" amtA of tokenA and amtB of tokenB from the sender
	*/
	function provideLiquidity( uint256 amtA, uint256 amtB ) public {
		require( amtA > 0 || amtB > 0, 'Cannot provide 0 liquidity' );
		//YOUR CODE HERE

    require(
    ERC20(tokenA).transferFrom(msg.sender, address(this), amtA),
    "Transfer of tokenA failed"
    );
    require(
        ERC20(tokenB).transferFrom(msg.sender, address(this), amtB),
        "Transfer of tokenB failed"
    );

    // Only set the initial invariant if it's the first provision
    if (invariant == 0) {
        invariant = ERC20(tokenA).balanceOf(address(this)) * ERC20(tokenB).balanceOf(address(this));
    } else {
        // Optionally enforce price ratio constraint here, if you want strict provisioning
        invariant = ERC20(tokenA).balanceOf(address(this)) * ERC20(tokenB).balanceOf(address(this));
    }

		emit LiquidityProvision( msg.sender, amtA, amtB );
	}

	/*
		Use the ERC20 transfer function to send amtA of tokenA and amtB of tokenB to the target recipient
		The modifier onlyRole(LP_ROLE) 
	*/
	function withdrawLiquidity( address recipient, uint256 amtA, uint256 amtB ) public onlyRole(LP_ROLE) {
		require( amtA > 0 || amtB > 0, 'Cannot withdraw 0' );
		require( recipient != address(0), 'Cannot withdraw to 0 address' );
		if( amtA > 0 ) {
			ERC20(tokenA).transfer(recipient,amtA);
		}
		if( amtB > 0 ) {
			ERC20(tokenB).transfer(recipient,amtB);
		}
		invariant = ERC20(tokenA).balanceOf(address(this))*ERC20(tokenB).balanceOf(address(this));
		emit Withdrawal( msg.sender, recipient, amtA, amtB );
	}


}
