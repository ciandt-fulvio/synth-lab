/**
 * TypeScript types for Tag.
 *
 * Types for tag API request/response handling.
 */

/**
 * Tag response.
 */
export interface Tag {
  /** Tag ID (tag_[a-f0-9]{8}) */
  id: string;
  /** Tag name */
  name: string;
}

/**
 * Request to create a new tag.
 */
export interface TagCreateRequest {
  /** Tag name (max 50 chars) */
  name: string;
}

/**
 * Request to add a tag to an experiment.
 */
export interface AddTagRequest {
  /** Name of the tag to add */
  tag_name: string;
}
