import { defineCollection, z } from 'astro:content';

const lessons = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    module: z.string(),
    moduleTitle: z.string(),
    chapter: z.string(),
    chapterTitle: z.string(),
    order: z.number(),
    description: z.string().optional(),
  }),
});

const readmes = defineCollection({
  type: 'content',
  schema: z.object({}).optional(),
});

export const collections = { lessons, readmes };
