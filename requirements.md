# Requirements — ShopSphere E-Commerce

## Domain Summary
Online retailer selling physical goods. Core processes: browse → cart → order → payment → fulfillment.

## Business Goals
- Unified reporting for sales, customers, and product performance
- Replace ad-hoc SQL with governed dbt models

## Pain Points
- Inconsistent revenue definitions across teams
- No single source of truth for customer lifetime value

## Business Questions
- What is total revenue and order count by month?
- Who are the top customers by lifetime spend?
- Which product categories drive the most revenue?

## Source Systems
- postgres database `shopsphere`, schema `ecommerce`
- Operational OLTP tables; nightly batch load

## Reporting Preferences
- Star schema for BI tools
- Semantic layer metrics for self-serve analytics
- Daily order grain; monthly executive rollups

## Constraints and Notes
- Exclude cancelled and fully refunded orders from revenue KPIs
- Currency assumed USD
