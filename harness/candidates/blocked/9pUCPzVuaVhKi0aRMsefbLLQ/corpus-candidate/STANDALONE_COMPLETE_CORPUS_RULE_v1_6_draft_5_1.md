# Standalone Complete Corpus Rule - v1.6 Draft 5.1

Status: active package rule.  
Generated: 2026-05-09.

## Rule

Every witness contract draft zip MUST be a complete standalone corpus. A reader
or implementer must be able to download only the current zip and implement the
current draft without retrieving any previous package.

## Requirements

1. The package carries forward all still-active earlier draft files.
2. The package includes the complete Draft 4.1 bridge layer.
3. The package includes the complete Draft 5 NLA witness layer.
4. The package includes the complete Draft 5.1 authority and self-training layer.
5. Versioned historical manifests and checksums may remain for traceability.
6. The active package manifest must list the complete final Draft 5.1 tree.
7. Summaries may not replace full contract bodies unless a newer full contract
   body supersedes them in the same package.

## Current package declaration

This corrected Draft 5.1 package was rebuilt from the uploaded Draft 5 corpus and
then overlaid with the Draft 5.1 authority/self-training additions. It supersedes
all earlier Draft 5.1 zips generated from Draft 4 or with abbreviated carry-forward
files.
