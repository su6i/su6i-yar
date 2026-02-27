---
name: js-ts-code-quality
description: JS/TS Code Quality Technical Encyclopedia: The industrial standard for TypeScript 5.7+ and Node.js 22+ development.
---

# Skill: JS/TS Code Quality (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for industrial-grade JavaScript and TypeScript development in the 2025 ecosystem. This document defines the standards for type-safety, code consistency, automated testing, and high-performance runtime optimization.

---

## 1. The TypeScript 5.7+ Standard: Strict-First Architecture
TypeScript is no longer a "preference" but a mandatory foundational layer. 2025 standards require fully strict configuration to eliminate the most common runtime failures.

### 1.1 `tsconfig.json` Technical Specification
Exhaustive strict-mode configuration for zero-compromise type integrity.
```json
{
  "compilerOptions": {
    "target": "ES2023",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    /* 1.1.1 Mandatory Strict Checks */
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "useUnknownInCatchVariables": true,
    "alwaysStrict": true,
    /* 1.1.2 Code Quality Checks */
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,
    /* 1.1.3 Advanced interop */
    "allowImportingTsExtensions": true,
    "rewriteRelativeImportExtensions": true
  }
}
```

---

## 2. Linting & Formatting (ESLint Flat Config & Prettier)
Moving from fragmented `.eslintrc` files to the "Flat Config" standard (`eslint.config.js`).

### 2.1 ESLint 9+ Flat Config Standard
Utilizing the Rust-powered `oxlint` or `eslint-plugin-perfectionist` for high-performance sorting and linting.
```javascript
import js from "@eslint/js";
import ts from "typescript-eslint";
import prettier from "eslint-config-prettier";
import perfectionist from "eslint-plugin-perfectionist";

export default ts.config(
  js.configs.recommended,
  ...ts.configs.recommendedTypeChecked,
  perfectionist.configs["recommended-alphabetical"],
  prettier, // 2.1.1 Disabling stylistic rules that conflict with Prettier
  {
    languageOptions: {
      parserOptions: {
        project: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      "@typescript-eslint/no-floating-promises": "error", // 2.1.2 Preventing fire-and-forget bugs
      "@typescript-eslint/await-thenable": "error",
      "@typescript-eslint/no-explicit-any": "warn",
    },
  }
);
```

### 2.2 Prettier Configuration
Standardizing the physical layout of code for git-diff consistency.
```json
{
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "semi": true,
  "singleQuote": true,
  "trailingComma": "all",
  "bracketSpacing": true,
  "arrowParens": "always",
  "plugins": ["prettier-plugin-tailwindcss"]
}
```

---

## 3. High-Performance Testing (Vitest 3.0+)
Standardizing on Vitest for its native ESM support, lightning-fast HMR (Hot Module Replacement), and integrated code coverage.

### 3.1 Test Implementation Protocol
*   **Unit Tests:** Testing individual functions in isolation with mock-driven dependencies.
*   **Integration Tests:** Testing the interaction between multiple modules or API layers.
*   **Property-Based Testing:** Utilizing `@fast-check/vitest` to generate thousands of random inputs to find edge-case failures.

```typescript
import { expect, test, vi } from 'vitest';
import { processOrder } from './orderService';

test('processOrder should apply 10% discount for VIP users', async () => {
    // 3.1.1 Mocking internal dependencies
    const mockDb = { save: vi.fn() };
    const user = { id: 1, isVip: true };
    const order = { amount: 100 };

    const result = await processOrder(mockDb, user, order);

    expect(result.finalAmount).toBe(90);
    expect(mockDb.save).toHaveBeenCalledOnce();
});
```

---

## 4. Advanced Design Patterns in TypeScript
Leveraging TS types to implement robust industrial patterns.

### 4.1 The Result Type (Railway-Oriented Programming)
Eliminating `try-catch` bloat in business logic.
```typescript
type Result<T, E> = { ok: true; value: T } | { ok: false; error: E };

function parseJson(input: string): Result<unknown, Error> {
    try {
        return { ok: true, value: JSON.parse(input) };
    } catch (e) {
        return { ok: false, error: e instanceof Error ? e : new Error('Unknown') };
    }
}
```

### 4.2 The Factory & Builder Patterns
Ensuring complex object creation is type-safe and consistent.

---

## 5. Performance Optimization: V8 Internals & Node.js 22+
Understanding how the runtime executes code to write "Hot-Path" optimized logic.

### 5.1 Hidden Classes & Inline Caches (ICs)
*   **Protocol:** Always initialize object properties in the same order inside constructors. This allows V8 to reuse the same "Hidden Class," preventing de-optimizations.
*   **Protocol:** Avoid `delete` on object properties; set them to `undefined` or `null` to maintain shape stability.

### 5.2 Worker Threads for CPU-Bound Logic
Moving heavy computations (e.g., image processing, encryption) out of the main event loop to prevent UI/API freezes.

---

## 6. Security Standards (OWASP for JS/TS)
*   **XSS Prevention:** Mandatory encoding of user-provided strings before DOM insertion.
*   **Prototype Pollution Defense:** Using `Object.create(null)` for plain objects that store untrusted keys.
*   **Dependency Auditing:** `npm audit` or `pnpm audit` integrated into CI/CD pipelines.

---

## 7. Technical Appendix: Advanced Type Logic
*   **Conditional Types:** `T extends string ? "S" : "N"`.
*   **Template Literal Types:** Dynamic string manipulation at compile-time (e.g., `type Route = `/user/${number}``).
*   **Branded Types:** Creating nominal types to prevent passing an `OrderId` to a function expecting a `UserId`.
    ```typescript
    type Brand<K, T> = K & { __brand: T };
    type UserId = Brand<number, 'UserId'>;
    ```

---

## 8. Verification & Benchmarking
*   **Coverage Threshold:** 90%+ globally.
*   **Build Size Metrics:** Pruning `devDependencies` and utilizing `treeshaking` in ESBuild/Rollup.
*   **Lighthouse Performance:** Score > 95 for frontend applications.

---
[Back to README](../../README.md)
