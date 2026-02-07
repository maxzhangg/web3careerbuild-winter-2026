// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract RewardDistributorBad {
    mapping(address => uint256) public rewards;

    // public + memory，循环里 users.length 每次都读
    function batchAddRewards(address[] memory users, uint256[] memory amounts) public {
        require(users.length == amounts.length, "len mismatch");

        for (uint256 i = 0; i < users.length; i++) {
            rewards[users[i]] += amounts[i];
        }
    }
}

contract RewardDistributorGood {
    mapping(address => uint256) public rewards;

    // external + calldata，缓存 len + 一次读一次写
    function batchAddRewards(address[] calldata users, uint256[] calldata amounts) external {
        uint256 len = users.length;
        require(len == amounts.length, "len mismatch");

        for (uint256 i = 0; i < len; ++i) {
            address u = users[i];
            uint256 addAmt = amounts[i];

            uint256 cur = rewards[u];
            rewards[u] = cur + addAmt;
        }
    }
}
